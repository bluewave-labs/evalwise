from celery import current_task
from celery_app import celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import uuid

from models import Run, Result, Evaluation, Item, Scenario, Evaluator
from adapters.factory import ModelAdapterFactory
from scenarios.factory import ScenarioGeneratorFactory
from evaluators.factory import EvaluatorFactory

# Database setup for Celery tasks
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://evalwise:evalwise123@localhost:5432/evalwise")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery.task(bind=True)
def process_run(self, run_id: str):
    """Process a complete evaluation run"""
    
    # Update task progress
    self.update_state(state='PROGRESS', meta={'current': 0, 'total': 0, 'status': 'Starting...'})
    
    db = SessionLocal()
    try:
        # Get run details
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            raise Exception(f"Run {run_id} not found")
        
        # Update run status
        run.status = "running"
        db.commit()
        
        # Get dataset items
        items = db.query(Item).filter(Item.dataset_id == run.dataset_id).all()
        if not items:
            raise Exception("No items found in dataset")
        
        # Get scenarios
        scenarios = db.query(Scenario).filter(Scenario.id.in_(run.scenario_ids)).all()
        if not scenarios:
            raise Exception("No scenarios found")
        
        # Get evaluators (from run's evaluator_ids - we need to add this field)
        # For now, get all evaluators as a placeholder
        evaluators = db.query(Evaluator).all()
        
        # Calculate total work
        total_tasks = len(items) * len(scenarios)
        completed_tasks = 0
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': completed_tasks, 
                'total': total_tasks, 
                'status': f'Processing {total_tasks} item-scenario combinations...'
            }
        )
        
        # Create model adapter
        adapter = ModelAdapterFactory.create_adapter(run.model_provider)
        
        # Process each item with each scenario
        for item in items:
            for scenario in scenarios:
                try:
                    # Process single item-scenario combination
                    result_id = asyncio.run(
                        process_item_scenario(
                            db, run, item, scenario, evaluators, adapter
                        )
                    )
                    
                    completed_tasks += 1
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': completed_tasks,
                            'total': total_tasks,
                            'status': f'Processed {completed_tasks}/{total_tasks} combinations'
                        }
                    )
                    
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error processing item {item.id} with scenario {scenario.id}: {str(e)}")
                    completed_tasks += 1
        
        # Mark run as completed
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        db.commit()
        
        return {
            'status': 'completed',
            'processed': completed_tasks,
            'total': total_tasks,
            'run_id': run_id
        }
        
    except Exception as e:
        # Mark run as failed
        if 'run' in locals():
            run.status = "failed"
            db.commit()
        
        raise Exception(f"Run processing failed: {str(e)}")
        
    finally:
        db.close()

async def process_item_scenario(
    db, run: Run, item: Item, scenario: Scenario, evaluators: List[Evaluator], adapter
) -> str:
    """Process a single item-scenario combination"""
    
    # Generate scenario prompt
    generator = ScenarioGeneratorFactory.create_generator(scenario.type, scenario.params_json)
    
    # Extract input text from item
    input_text = ""
    if isinstance(item.input_json, dict):
        # Try common keys
        input_text = (
            item.input_json.get("question") or
            item.input_json.get("prompt") or
            item.input_json.get("text") or
            str(item.input_json)
        )
    else:
        input_text = str(item.input_json)
    
    # Generate adversarial prompt
    adversarial_prompt = generator.generate_prompt(input_text, item.metadata_json)
    
    try:
        # Call model
        model_response = await adapter.generate(
            prompt=adversarial_prompt,
            model_name=run.model_name,
            **run.model_params_json
        )
        
        # Create result record
        result = Result(
            run_id=run.id,
            item_id=item.id,
            scenario_id=scenario.id,
            output_json={"content": model_response.content},
            latency_ms=model_response.latency_ms,
            token_input=model_response.token_input,
            token_output=model_response.token_output,
            cost_usd=model_response.cost_usd
        )
        db.add(result)
        db.flush()  # Get the result ID
        
        # Run evaluators
        for evaluator in evaluators:
            try:
                # Create evaluator instance
                eval_instance = EvaluatorFactory.create_evaluator(
                    evaluator.kind, evaluator.config_json
                )
                
                # Extract expected output
                expected_output = None
                if item.expected_json:
                    if isinstance(item.expected_json, dict):
                        expected_output = (
                            item.expected_json.get("answer") or
                            item.expected_json.get("response") or
                            item.expected_json.get("expected") or
                            str(item.expected_json)
                        )
                    else:
                        expected_output = str(item.expected_json)
                
                # Run evaluation
                eval_result = await eval_instance.evaluate(
                    input_text=adversarial_prompt,
                    output_text=model_response.content,
                    expected_output=expected_output,
                    metadata=item.metadata_json
                )
                
                # Store evaluation
                evaluation = Evaluation(
                    result_id=result.id,
                    evaluator_id=evaluator.id,
                    score_float=eval_result.score,
                    pass_bool=eval_result.pass_fail,
                    notes_text=eval_result.notes,
                    raw_json=eval_result.raw_data
                )
                db.add(evaluation)
                
            except Exception as e:
                print(f"Evaluator {evaluator.name} failed: {str(e)}")
                # Create error evaluation record
                evaluation = Evaluation(
                    result_id=result.id,
                    evaluator_id=evaluator.id,
                    score_float=0.0,
                    pass_bool=False,
                    notes_text=f"Evaluation error: {str(e)}",
                    raw_json={"error": str(e)}
                )
                db.add(evaluation)
        
        db.commit()
        return str(result.id)
        
    except Exception as e:
        # Create failed result record
        result = Result(
            run_id=run.id,
            item_id=item.id,
            scenario_id=scenario.id,
            output_json={"error": str(e)},
            latency_ms=0,
            token_input=0,
            token_output=0,
            cost_usd=0.0
        )
        db.add(result)
        db.commit()
        
        raise e

@celery.task
def get_task_status(task_id: str):
    """Get status of a task"""
    result = celery.AsyncResult(task_id)
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result,
        'info': result.info
    }