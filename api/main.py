from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import pandas as pd
import io
import uuid

from database import get_db, engine
from utils.file_validation import FileValidator
from models import Base, Dataset, Item, Scenario, Evaluator, Run, Result, Evaluation, User, Organization
from schemas import (
    DatasetCreate, DatasetResponse, ItemCreate, ItemResponse,
    ScenarioCreate, ScenarioResponse, EvaluatorCreate, EvaluatorResponse,
    RunCreate, RunResponse, ResultResponse, RunAggregates,
    PlaygroundRequest, PlaygroundResponse
)
from auth.routes import router as auth_router
from auth.admin_routes import router as admin_router
from auth.security import get_current_user

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EvalWise API", version="1.0.0")

# CORS middleware
from config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(admin_router, tags=["admin"])

# Dashboard metrics endpoint
@app.get("/dashboard/metrics")
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard metrics for the current user."""
    
    # Get basic counts
    total_datasets = db.query(Dataset).count()
    total_scenarios = db.query(Scenario).count()
    total_evaluators = db.query(Evaluator).count()
    total_runs = db.query(Run).count()
    
    # Get recent runs (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_runs = db.query(Run).filter(Run.created_at >= thirty_days_ago).count()
    
    # Get run status distribution
    pending_runs = db.query(Run).filter(Run.status == "pending").count()
    running_runs = db.query(Run).filter(Run.status == "running").count()
    completed_runs = db.query(Run).filter(Run.status == "completed").count()
    failed_runs = db.query(Run).filter(Run.status == "failed").count()
    
    # Get evaluation results summary (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_evaluations = db.query(Evaluation).join(Run).filter(
        Run.created_at >= seven_days_ago
    ).all()
    
    passed_evaluations = sum(1 for eval in recent_evaluations if eval.pass_bool)
    failed_evaluations = len(recent_evaluations) - passed_evaluations
    
    # Calculate pass rates by evaluator category
    evaluator_stats = {}
    for evaluation in recent_evaluations:
        evaluator = db.query(Evaluator).filter(Evaluator.id == evaluation.evaluator_id).first()
        if evaluator:
            category = evaluator.kind
            if category not in evaluator_stats:
                evaluator_stats[category] = {"passed": 0, "total": 0}
            evaluator_stats[category]["total"] += 1
            if evaluation.pass_bool:
                evaluator_stats[category]["passed"] += 1
    
    # Calculate pass rates
    pass_rates_by_category = {}
    for category, stats in evaluator_stats.items():
        if stats["total"] > 0:
            pass_rates_by_category[category] = round((stats["passed"] / stats["total"]) * 100, 1)
    
    # Get most active datasets (by runs)
    active_datasets = db.query(
        Dataset.name,
        func.count(Run.id).label('run_count')
    ).join(Run).group_by(Dataset.id, Dataset.name).order_by(
        func.count(Run.id).desc()
    ).limit(5).all()
    
    return {
        "totals": {
            "datasets": total_datasets,
            "scenarios": total_scenarios,
            "evaluators": total_evaluators,
            "runs": total_runs,
            "recent_runs": recent_runs
        },
        "run_status": {
            "pending": pending_runs,
            "running": running_runs,
            "completed": completed_runs,
            "failed": failed_runs
        },
        "recent_evaluations": {
            "passed": passed_evaluations,
            "failed": failed_evaluations,
            "total": len(recent_evaluations)
        },
        "pass_rates_by_category": pass_rates_by_category,
        "active_datasets": [
            {"name": dataset[0], "runs": dataset[1]} 
            for dataset in active_datasets
        ]
    }

# Datasets endpoints
@app.post("/datasets", response_model=DatasetResponse)
def create_dataset(
    dataset: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate version hash using SHA256 instead of MD5
    content = json.dumps({"name": dataset.name, "tags": sorted(dataset.tags)}, sort_keys=True)
    version_hash = hashlib.sha256(content.encode()).hexdigest()
    
    db_dataset = Dataset(
        name=dataset.name,
        version_hash=version_hash,
        tags=dataset.tags,
        is_synthetic=dataset.is_synthetic
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

@app.get("/datasets", response_model=List[DatasetResponse])
def list_datasets(
    tag: Optional[str] = None,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Dataset)
    
    if tag:
        query = query.filter(Dataset.tags.contains([tag]))
    
    if q:
        query = query.filter(Dataset.name.ilike(f"%{q}%"))
    
    return query.all()

@app.get("/datasets/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@app.post("/datasets/{dataset_id}/items", response_model=dict)
async def upload_items(
    dataset_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Validate file upload with comprehensive security checks
        content = await FileValidator.validate_upload_file(
            file, 
            allowed_extensions=['.csv', '.jsonl']
        )
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith('.jsonl'):
            df = pd.read_json(io.BytesIO(content), lines=True)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        items_created = 0
        for _, row in df.iterrows():
            # Extract input, expected, metadata from row
            input_data = {}
            expected_data = {}
            metadata_data = {}
            
            for col in df.columns:
                if col.startswith('input.'):
                    key = col[6:]  # Remove 'input.' prefix
                    input_data[key] = row[col]
                elif col.startswith('expected.'):
                    key = col[9:]  # Remove 'expected.' prefix
                    expected_data[key] = row[col]
                elif col.startswith('metadata.'):
                    key = col[9:]  # Remove 'metadata.' prefix
                    metadata_data[key] = row[col]
                else:
                    # Default to input
                    input_data[col] = row[col]
            
            db_item = Item(
                dataset_id=dataset_id,
                input_json=input_data,
                expected_json=expected_data if expected_data else None,
                metadata_json=metadata_data
            )
            db.add(db_item)
            items_created += 1
        
        db.commit()

        # Update dataset version hash using SHA256
        items_hash = hashlib.sha256(str(items_created).encode()).hexdigest()
        dataset.version_hash = hashlib.sha256(f"{dataset.version_hash}{items_hash}".encode()).hexdigest()
        db.commit()
        
        return {"message": f"Uploaded {items_created} items successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# Scenarios endpoints
@app.post("/scenarios", response_model=ScenarioResponse)
def create_scenario(
    scenario: ScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_scenario = Scenario(
        name=scenario.name,
        type=scenario.type,
        params_json=scenario.params,
        tags=scenario.tags
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

@app.get("/scenarios", response_model=List[ScenarioResponse])
def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Scenario).all()

# Evaluators endpoints
@app.post("/evaluators", response_model=EvaluatorResponse)
def create_evaluator(
    evaluator: EvaluatorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_evaluator = Evaluator(
        name=evaluator.name,
        kind=evaluator.kind,
        config_json=evaluator.config
    )
    db.add(db_evaluator)
    db.commit()
    db.refresh(db_evaluator)
    return db_evaluator

@app.get("/evaluators", response_model=List[EvaluatorResponse])
def list_evaluators(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Evaluator).all()

# Runs endpoints
@app.post("/runs", response_model=RunResponse)
def create_run(
    run: RunCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == run.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Validate scenarios exist
    scenarios = db.query(Scenario).filter(Scenario.id.in_(run.scenario_ids)).all()
    if len(scenarios) != len(run.scenario_ids):
        raise HTTPException(status_code=404, detail="One or more scenarios not found")
    
    # Validate evaluators exist
    evaluators = db.query(Evaluator).filter(Evaluator.id.in_(run.evaluator_ids)).all()
    if len(evaluators) != len(run.evaluator_ids):
        raise HTTPException(status_code=404, detail="One or more evaluators not found")
    
    db_run = Run(
        name=run.name,
        dataset_id=run.dataset_id,
        dataset_version_hash=dataset.version_hash,
        scenario_ids=[str(sid) for sid in run.scenario_ids],
        model_provider=run.model.provider,
        model_name=run.model.name,
        model_params_json=run.model.params,
        status="pending"
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    
    # Trigger celery job to process run
    from tasks.evaluation import process_run
    task = process_run.delay(str(db_run.id))
    
    return db_run

@app.get("/runs", response_model=List[RunResponse])
def list_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Run).all()

@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.get("/runs/{run_id}/results", response_model=List[ResultResponse])
def get_run_results(
    run_id: uuid.UUID,
    evaluator_id: Optional[uuid.UUID] = None,
    scenario_id: Optional[uuid.UUID] = None,
    pass_filter: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Result).filter(Result.run_id == run_id)
    
    if evaluator_id:
        query = query.join(Evaluation).filter(Evaluation.evaluator_id == evaluator_id)
    
    if scenario_id:
        query = query.filter(Result.scenario_id == scenario_id)
    
    if pass_filter is not None:
        query = query.join(Evaluation).filter(Evaluation.pass_bool == pass_filter)
    
    return query.all()

@app.get("/runs/{run_id}/aggregates", response_model=RunAggregates)
def get_run_aggregates(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # This would calculate aggregates from results
    # Implementation simplified for now
    return RunAggregates(
        total_results=0,
        pass_rate_overall=0.0,
        pass_rate_by_evaluator={},
        pass_rate_by_scenario={},
        mean_score_by_evaluator={},
        mean_latency_ms=0.0,
        total_cost_usd=0.0
    )

# Playground endpoint
@app.post("/playground/test", response_model=PlaygroundResponse)
def playground_test(
    request: PlaygroundRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # TODO: Implement playground testing
    # This would call the model and run evaluators
    return PlaygroundResponse(
        output="Sample response",
        latency_ms=1000,
        token_input=10,
        token_output=20,
        cost_usd=0.001,
        evaluations=[]
    )

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)