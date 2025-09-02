from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
import uuid

# Import database and models
from database import get_db, engine
from models import Base, Dataset, Item, Scenario, Evaluator, Run, Result, Evaluation
from auth.models import User, Organization, UserOrganization
from schemas_simple import DatasetCreate, ScenarioCreate, EvaluatorCreate, RunCreate, PlaygroundRequest

# Import authentication
from auth.routes import router as auth_router
from auth.admin_routes import router as admin_router
from auth.security import get_current_user_flexible

# Import logging and error handling
from utils.logging import get_logger, RequestContext
from utils.errors import NotFoundError, ValidationError, ErrorResponse, ErrorDetail, InternalServerError
from middleware import RequestTrackingMiddleware, ErrorHandlingMiddleware
from middleware.security import SecurityHeadersMiddleware
from middleware.rate_limiting import RateLimitingMiddleware
from middleware.validation import APIValidationMiddleware
from config import settings

# Initialize logger
logger = get_logger(__name__)

# Validate startup configuration (disabled for testing)
# from utils.startup_validation import validate_startup
# validate_startup()

app = FastAPI(
    title="EvalWise API", 
    version="1.0.0", 
    description="LLM Red Teaming & Evaluation Platform"
)

# Add middleware (order matters - last added runs first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(APIValidationMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestTrackingMiddleware)

# CORS middleware with secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    details = []
    for error in exc.errors():
        details.append(ErrorDetail(
            code="VALIDATION_ERROR",
            message=error['msg'],
            field='.'.join(str(loc) for loc in error['loc']),
            details=error
        ))
    
    error_response = ErrorResponse(
        message="Validation failed",
        details=details,
        request_id=request_id
    )
    
    logger.warning(
        f"Validation error in {request.method} {request.url.path}",
        extra={'request_id': request_id, 'errors': exc.errors()}
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict(),
        headers={'X-Request-ID': request_id}
    )

# Include authentication router
app.include_router(auth_router)
app.include_router(admin_router)

@app.get("/health")
def health_check(request: Request):
    """Health check endpoint"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info("Health check requested", extra={'request_id': request_id})
    
    return {
        "status": "healthy", 
        "message": "EvalWise API is running",
        "version": "1.0.0",
        "environment": settings.environment,
        "request_id": request_id
    }

@app.get("/dashboard/metrics")
def get_dashboard_metrics(
    request: Request,
    current_user = Depends(get_current_user_flexible),
    db: Session = Depends(get_db)
):
    """Get dashboard metrics for the current user."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info("Dashboard metrics requested", extra={'request_id': request_id})
    
    try:
        # Get basic counts
        total_datasets = db.query(Dataset).count()
        total_scenarios = db.query(Scenario).count()
        total_evaluators = db.query(Evaluator).count()
        total_runs = db.query(Run).count()
        
        # Get recent runs (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_runs = db.query(Run).filter(Run.started_at >= thirty_days_ago).count()
        
        # Get run status distribution
        pending_runs = db.query(Run).filter(Run.status == "pending").count()
        running_runs = db.query(Run).filter(Run.status == "running").count()
        completed_runs = db.query(Run).filter(Run.status == "completed").count()
        failed_runs = db.query(Run).filter(Run.status == "failed").count()
        
        # Get evaluation results summary (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_evaluations = db.query(Evaluation).join(Result).join(Run).filter(
            Run.started_at >= seven_days_ago
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
        
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}", extra={'request_id': request_id})
        raise InternalServerError(f"Failed to fetch dashboard metrics: {str(e)}")

# Dataset endpoints
@app.get("/datasets")
def list_datasets(
    tag: Optional[str] = None, 
    q: Optional[str] = None, 
    request: Request = None, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """List all datasets with optional filtering"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
    
    logger.info("Listing datasets", extra={
        'request_id': request_id, 
        'tag': tag, 
        'query': q
    })
    
    try:
        query = db.query(Dataset)
        
        if tag:
            query = query.filter(Dataset.tags.contains([tag]))
        
        if q:
            query = query.filter(Dataset.name.ilike(f"%{q}%"))
        
        datasets = query.all()
        
        result = []
        for dataset in datasets:
            try:
                result.append({
                    "id": str(dataset.id),
                    "name": dataset.name,
                    "version_hash": dataset.version_hash,
                    "tags": dataset.tags or [],
                    "schema_json": dataset.schema_json,
                    "is_synthetic": dataset.is_synthetic,
                    "created_at": dataset.created_at.isoformat() if dataset.created_at else None
                })
            except Exception as e:
                logger.error(f"Error processing dataset {dataset.id}: {str(e)}", extra={'request_id': request_id})
                # Skip this dataset but continue with others
                continue
                
        logger.info(f"Retrieved {len(result)} datasets", extra={'request_id': request_id})
        return result
        
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}", extra={'request_id': request_id})
        raise InternalServerError("Failed to retrieve datasets", request_id=request_id)

@app.post("/datasets")
def create_dataset(
    dataset_data: DatasetCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Create a new dataset"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.info(
        f"Creating dataset: {dataset_data.name}",
        extra={'request_id': request_id, 'user_id': str(current_user.id)}
    )
    
    try:
        # Generate version hash
        content = json.dumps({"name": dataset_data.name, "tags": sorted(dataset_data.tags)}, sort_keys=True)
        version_hash = hashlib.md5(content.encode()).hexdigest()
        
        dataset = Dataset(
            name=dataset_data.name,
            version_hash=version_hash,
            tags=dataset_data.tags,
            is_synthetic=dataset_data.is_synthetic
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        logger.info(
            f"Dataset created successfully: {dataset.name}",
            extra={'request_id': request_id, 'dataset_id': str(dataset.id)}
        )
    except Exception as e:
        logger.error(
            f"Error creating dataset: {str(e)}",
            extra={'request_id': request_id}
        )
        raise InternalServerError("Failed to create dataset", request_id=request_id)
    
    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "version_hash": dataset.version_hash,
        "tags": dataset.tags or [],
        "is_synthetic": dataset.is_synthetic,
        "created_at": dataset.created_at.isoformat()
    }

@app.get("/datasets/{dataset_id}")
def get_dataset(
    dataset_id: str, 
    request: Request, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Get a specific dataset"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        logger.warning(
            f"Invalid dataset ID format: {dataset_id}",
            extra={'request_id': request_id, 'dataset_id': dataset_id}
        )
        raise ValidationError(
            message="Invalid dataset ID format",
            details=[ErrorDetail(
                code="INVALID_UUID",
                message="Dataset ID must be a valid UUID",
                field="dataset_id"
            )],
            request_id=request_id
        )
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_uuid).first()
    if not dataset:
        logger.warning(
            f"Dataset not found: {dataset_id}",
            extra={'request_id': request_id, 'dataset_id': dataset_id}
        )
        raise NotFoundError("Dataset", dataset_id, request_id)
    
    # Get item count
    item_count = db.query(Item).filter(Item.dataset_id == dataset_uuid).count()
    
    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "version_hash": dataset.version_hash,
        "tags": dataset.tags or [],
        "schema_json": dataset.schema_json,
        "is_synthetic": dataset.is_synthetic,
        "created_at": dataset.created_at.isoformat(),
        "item_count": item_count
    }

@app.post("/datasets/{dataset_id}/upload")
async def upload_dataset_items(
    dataset_id: str,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Upload CSV/JSONL items to a dataset"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
    
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise ValidationError(
            message="Invalid dataset ID format",
            details=[ErrorDetail(
                code="INVALID_UUID",
                message="Dataset ID must be a valid UUID",
                field="dataset_id"
            )],
            request_id=request_id
        )
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_uuid).first()
    if not dataset:
        raise NotFoundError("Dataset", dataset_id, request_id)
    
    try:
        # Import here to avoid circular imports  
        from utils.file_validation import FileValidator
        import pandas as pd
        import io
        
        # Validate file upload with comprehensive security checks
        content = await FileValidator.validate_upload_file(
            file, 
            allowed_extensions=['.csv', '.jsonl']
        )
        
        # Parse file based on extension
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith('.jsonl'):
            df = pd.read_json(io.BytesIO(content), lines=True)
        else:
            raise ValidationError(
                message="Unsupported file format",
                details=[ErrorDetail(
                    code="INVALID_FILE_TYPE",
                    message="Only CSV and JSONL files are supported",
                    field="file"
                )],
                request_id=request_id
            )
        
        items_created = 0
        for _, row in df.iterrows():
            # Extract input, expected, metadata from row
            input_data = {}
            expected_data = {}
            metadata_data = {}
            
            for col in df.columns:
                cell_value = row[col]
                # Skip NaN values
                if pd.isna(cell_value):
                    continue
                    
                if col.startswith('input.'):
                    key = col[6:]  # Remove 'input.' prefix
                    input_data[key] = cell_value
                elif col.startswith('expected.'):
                    key = col[9:]  # Remove 'expected.' prefix
                    expected_data[key] = cell_value
                elif col.startswith('metadata.'):
                    key = col[9:]  # Remove 'metadata.' prefix
                    metadata_data[key] = cell_value
                else:
                    # Default to input
                    input_data[col] = cell_value
            
            # Create item
            db_item = Item(
                dataset_id=dataset_uuid,
                input_json=input_data,
                expected_json=expected_data if expected_data else None,
                metadata_json=metadata_data if metadata_data else None
            )
            db.add(db_item)
            items_created += 1
        
        db.commit()
        
        logger.info(
            f"Successfully uploaded {items_created} items to dataset {dataset_id}",
            extra={'request_id': request_id, 'dataset_id': dataset_id, 'items_count': items_created}
        )
        
        return {
            "message": f"Successfully uploaded {items_created} items",
            "items_created": items_created,
            "dataset_id": dataset_id
        }
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error uploading dataset items: {str(e)}",
            extra={'request_id': request_id, 'dataset_id': dataset_id}
        )
        raise InternalServerError(f"Failed to upload dataset items: {str(e)}")

# Scenario endpoints
@app.get("/scenarios")
def list_scenarios(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """List all scenarios"""
    scenarios = db.query(Scenario).all()
    return [
        {
            "id": str(scenario.id),
            "name": scenario.name,
            "type": scenario.type,
            "params_json": scenario.params_json or {},
            "tags": scenario.tags or [],
            "created_at": scenario.created_at.isoformat()
        }
        for scenario in scenarios
    ]

@app.post("/scenarios")
def create_scenario(
    scenario_data: ScenarioCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Create a new scenario"""
    scenario = Scenario(
        name=scenario_data.name,
        type=scenario_data.type,
        params_json=scenario_data.params,
        tags=scenario_data.tags
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    
    return {
        "id": str(scenario.id),
        "name": scenario.name,
        "type": scenario.type,
        "params_json": scenario.params_json or {},
        "tags": scenario.tags or [],
        "created_at": scenario.created_at.isoformat()
    }

# Evaluator endpoints
@app.get("/evaluators")
def list_evaluators(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """List all evaluators"""
    evaluators = db.query(Evaluator).all()
    return [
        {
            "id": str(evaluator.id),
            "name": evaluator.name,
            "kind": evaluator.kind,
            "config_json": evaluator.config_json or {},
            "created_at": evaluator.created_at.isoformat()
        }
        for evaluator in evaluators
    ]

@app.post("/evaluators")
def create_evaluator(
    evaluator_data: EvaluatorCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Create a new evaluator"""
    evaluator = Evaluator(
        name=evaluator_data.name,
        kind=evaluator_data.kind,
        config_json=evaluator_data.config
    )
    db.add(evaluator)
    db.commit()
    db.refresh(evaluator)
    
    return {
        "id": str(evaluator.id),
        "name": evaluator.name,
        "kind": evaluator.kind,
        "config_json": evaluator.config_json or {},
        "created_at": evaluator.created_at.isoformat()
    }

# Run endpoints
@app.get("/runs")
def list_runs(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """List all runs"""
    runs = db.query(Run).all()
    return [
        {
            "id": str(run.id),
            "name": run.name,
            "dataset_id": str(run.dataset_id),
            "dataset_version_hash": run.dataset_version_hash,
            "scenario_ids": [str(sid) for sid in (run.scenario_ids or [])],
            "model_provider": run.model_provider,
            "model_name": run.model_name,
            "model_params_json": run.model_params_json or {},
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "status": run.status,
            "owner": run.owner
        }
        for run in runs
    ]

@app.post("/runs")
def create_run(
    run_data: RunCreate, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Create a new evaluation run"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Validate dataset exists
    try:
        dataset_uuid = uuid.UUID(run_data.dataset_id)
    except ValueError:
        raise ValidationError(
            message="Invalid dataset ID format",
            details=[ErrorDetail(
                code="INVALID_UUID",
                message="Dataset ID must be a valid UUID",
                field="dataset_id"
            )],
            request_id=request_id
        )
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_uuid).first()
    if not dataset:
        raise NotFoundError("Dataset", run_data.dataset_id, request_id)
    
    # Validate scenarios exist
    scenario_uuids = []
    for sid in run_data.scenario_ids:
        try:
            scenario_uuid = uuid.UUID(sid)
            scenario_uuids.append(scenario_uuid)
        except ValueError:
            raise ValidationError(
                message="Invalid scenario ID format",
                details=[ErrorDetail(
                    code="INVALID_UUID",
                    message=f"Scenario ID must be a valid UUID: {sid}",
                    field="scenario_ids"
                )],
                request_id=request_id
            )
    
    if scenario_uuids:
        scenarios = db.query(Scenario).filter(Scenario.id.in_(scenario_uuids)).all()
        if len(scenarios) != len(scenario_uuids):
            raise NotFoundError("One or more scenarios", request_id=request_id)
    
    run = Run(
        name=run_data.name,
        dataset_id=dataset_uuid,
        dataset_version_hash=dataset.version_hash,
        scenario_ids=scenario_uuids,
        model_provider=run_data.model_provider,
        model_name=run_data.model_name,
        model_params_json=run_data.model_params,
        status="pending",
        owner=current_user.username
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    return {
        "id": str(run.id),
        "name": run.name,
        "dataset_id": str(run.dataset_id),
        "dataset_version_hash": run.dataset_version_hash,
        "scenario_ids": [str(sid) for sid in (run.scenario_ids or [])],
        "model_provider": run.model_provider,
        "model_name": run.model_name,
        "model_params_json": run.model_params_json or {},
        "started_at": run.started_at.isoformat(),
        "status": run.status
    }

@app.get("/runs/{run_id}")
def get_run(
    run_id: str, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Get a specific run"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise ValidationError(
            message="Invalid run ID format",
            details=[ErrorDetail(
                code="INVALID_UUID",
                message="Run ID must be a valid UUID",
                field="run_id"
            )],
            request_id=request_id
        )
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise NotFoundError("Run", run_id, request_id)
    
    return {
        "id": str(run.id),
        "name": run.name,
        "dataset_id": str(run.dataset_id),
        "dataset_version_hash": run.dataset_version_hash,
        "scenario_ids": [str(sid) for sid in (run.scenario_ids or [])],
        "model_provider": run.model_provider,
        "model_name": run.model_name,
        "model_params_json": run.model_params_json or {},
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "status": run.status,
        "owner": run.owner
    }

@app.get("/runs/{run_id}/results")
def get_run_results(
    run_id: str, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Get results and evaluations for a specific run"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise ValidationError(
            message="Invalid run ID format",
            details=[ErrorDetail(
                code="INVALID_UUID",
                message="Run ID must be a valid UUID",
                field="run_id"
            )],
            request_id=request_id
        )
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise NotFoundError("Run", run_id, request_id)
    
    # Get results with evaluations
    results = db.query(Result).filter(Result.run_id == run_uuid).all()
    
    result_data = []
    for result in results:
        # Get evaluations for this result
        evaluations = db.query(Evaluation).filter(Evaluation.result_id == result.id).all()
        
        evaluation_data = []
        for eval_result in evaluations:
            evaluator = db.query(Evaluator).filter(Evaluator.id == eval_result.evaluator_id).first()
            evaluation_data.append({
                "evaluator_id": str(eval_result.evaluator_id),
                "evaluator_name": evaluator.name if evaluator else "Unknown",
                "evaluator_kind": evaluator.kind if evaluator else "Unknown",
                "score": eval_result.score_float,
                "pass": eval_result.pass_bool,
                "notes": eval_result.notes_text,
                "raw_data": eval_result.raw_json
            })
        
        result_data.append({
            "id": str(result.id),
            "item_id": str(result.item_id),
            "scenario_id": str(result.scenario_id) if result.scenario_id else None,
            "output": result.output_json,
            "latency_ms": result.latency_ms,
            "token_input": result.token_input,
            "token_output": result.token_output,
            "cost_usd": result.cost_usd,
            "created_at": result.created_at.isoformat(),
            "evaluations": evaluation_data
        })
    
    return {
        "run_id": str(run.id),
        "run_name": run.name,
        "run_status": run.status,
        "total_results": len(result_data),
        "results": result_data
    }

# Evaluation endpoints
@app.post("/runs/{run_id}/execute") 
def start_run(
    run_id: str, 
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Start processing an evaluation run"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise ValidationError(
            message="Invalid run ID format",
            details=[ErrorDetail(
                code="INVALID_UUID",
                message="Run ID must be a valid UUID",
                field="run_id"
            )],
            request_id=request_id
        )
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise NotFoundError("Run", run_id, request_id)
    
    if run.status != "pending":
        raise ValidationError(
            message=f"Cannot start run that is already {run.status}",
            details=[ErrorDetail(
                code="INVALID_STATUS",
                message=f"Run status must be 'pending', currently '{run.status}'",
                field="status"
            )],
            request_id=request_id
        )
    
    # Import the task here to avoid circular imports
    from tasks.simple_evaluation import process_simple_run
    
    # Start the Celery task
    task = process_simple_run.delay(run_id)
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "Evaluation run started"
    }

@app.get("/tasks/{task_id}/status")
def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user_flexible)
):
    """Get the status of a Celery task"""
    from celery_app import celery
    
    result = celery.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
        "info": result.info
    }

@app.post("/test/evaluators")
def test_evaluators(
    current_user = Depends(get_current_user_flexible)
):
    """Test evaluators with sample data"""
    from tasks.simple_evaluation import test_evaluators
    
    task = test_evaluators.delay()
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "Evaluator test started"
    }

# Playground endpoint (simplified for now)
@app.post("/playground/test")
def playground_test(
    request: PlaygroundRequest,
    current_user = Depends(get_current_user_flexible)
):
    """Test a single prompt (placeholder implementation)"""
    return {
        "output": f"Mock response to: {request.prompt[:50]}...",
        "latency_ms": 1000,
        "token_input": 10,
        "token_output": 20,
        "cost_usd": 0.001,
        "evaluations": [
            {
                "evaluator_id": eid,
                "score_float": 0.8,
                "pass_bool": True,
                "notes_text": "Mock evaluation result"
            }
            for eid in request.evaluator_ids[:2]  # Limit to first 2
        ]
    }

# Organization endpoints
@app.post("/organizations")
async def create_organization(
    request: Request,
    name: str = Body(...),
    description: str = Body(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """Create a new organization"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())) if request else str(uuid.uuid4())
    
    org = Organization(
        id=uuid.uuid4(),
        name=name,
        description=description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(org)
    
    # Add user to organization as admin
    user_org = UserOrganization(
        id=uuid.uuid4(),
        user_id=current_user.id,
        organization_id=org.id,
        role="admin",
        joined_at=datetime.utcnow()
    )
    
    db.add(user_org)
    db.commit()
    
    return {
        "id": str(org.id),
        "name": org.name,
        "description": org.description,
        "created_at": org.created_at.isoformat()
    }

@app.get("/organizations")
async def list_organizations(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_flexible)
):
    """List organizations for the current user"""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())) if request else str(uuid.uuid4())
    
    user_orgs = db.query(UserOrganization).filter(UserOrganization.user_id == current_user.id).all()
    organizations = []
    
    for user_org in user_orgs:
        org = db.query(Organization).filter(Organization.id == user_org.organization_id).first()
        if org:
            organizations.append({
                "id": str(org.id),
                "name": org.name,
                "description": org.description,
                "role": user_org.role,
                "created_at": org.created_at.isoformat()
            })
    
    return organizations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

