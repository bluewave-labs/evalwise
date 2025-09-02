from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
import json
import uuid

# Import database and models
from database import get_db, engine
from models import Base, Dataset, Item, Scenario, Evaluator, Run

app = FastAPI(title="EvalWise API", version="1.0.0", description="LLM Red Teaming & Evaluation Platform")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "EvalWise API is running"}

# Dataset endpoints
@app.get("/datasets")
def list_datasets(tag: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    """List all datasets with optional filtering"""
    query = db.query(Dataset)
    
    if tag:
        query = query.filter(Dataset.tags.contains([tag]))
    
    if q:
        query = query.filter(Dataset.name.ilike(f"%{q}%"))
    
    datasets = query.all()
    return [
        {
            "id": str(dataset.id),
            "name": dataset.name,
            "version_hash": dataset.version_hash,
            "tags": dataset.tags or [],
            "schema_json": dataset.schema_json,
            "is_synthetic": dataset.is_synthetic,
            "created_at": dataset.created_at.isoformat()
        }
        for dataset in datasets
    ]

@app.post("/datasets")
def create_dataset(
    name: str,
    tags: List[str] = None,
    is_synthetic: bool = False,
    db: Session = Depends(get_db)
):
    """Create a new dataset"""
    if tags is None:
        tags = []
    
    # Generate version hash
    content = json.dumps({"name": name, "tags": sorted(tags)}, sort_keys=True)
    version_hash = hashlib.md5(content.encode()).hexdigest()
    
    dataset = Dataset(
        name=name,
        version_hash=version_hash,
        tags=tags,
        is_synthetic=is_synthetic
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "version_hash": dataset.version_hash,
        "tags": dataset.tags or [],
        "is_synthetic": dataset.is_synthetic,
        "created_at": dataset.created_at.isoformat()
    }

@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get a specific dataset"""
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_uuid).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
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

# Scenario endpoints
@app.get("/scenarios")
def list_scenarios(db: Session = Depends(get_db)):
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
    name: str,
    type: str,
    params: dict = None,
    tags: List[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new scenario"""
    if params is None:
        params = {}
    if tags is None:
        tags = []
    
    scenario = Scenario(
        name=name,
        type=type,
        params_json=params,
        tags=tags
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
def list_evaluators(db: Session = Depends(get_db)):
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
    name: str,
    kind: str,
    config: dict = None,
    db: Session = Depends(get_db)
):
    """Create a new evaluator"""
    if config is None:
        config = {}
    
    evaluator = Evaluator(
        name=name,
        kind=kind,
        config_json=config
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
def list_runs(db: Session = Depends(get_db)):
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
    name: Optional[str] = None,
    dataset_id: str = None,
    scenario_ids: List[str] = None,
    model_provider: str = "openai",
    model_name: str = "gpt-3.5-turbo",
    model_params: dict = None,
    db: Session = Depends(get_db)
):
    """Create a new evaluation run"""
    if dataset_id is None:
        raise HTTPException(status_code=400, detail="dataset_id is required")
    if scenario_ids is None:
        scenario_ids = []
    if model_params is None:
        model_params = {}
    
    # Validate dataset exists
    try:
        dataset_uuid = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dataset ID format")
    
    dataset = db.query(Dataset).filter(Dataset.id == dataset_uuid).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Validate scenarios exist
    scenario_uuids = []
    for sid in scenario_ids:
        try:
            scenario_uuid = uuid.UUID(sid)
            scenario_uuids.append(scenario_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid scenario ID format: {sid}")
    
    if scenario_uuids:
        scenarios = db.query(Scenario).filter(Scenario.id.in_(scenario_uuids)).all()
        if len(scenarios) != len(scenario_uuids):
            raise HTTPException(status_code=404, detail="One or more scenarios not found")
    
    run = Run(
        name=name,
        dataset_id=dataset_uuid,
        dataset_version_hash=dataset.version_hash,
        scenario_ids=scenario_uuids,
        model_provider=model_provider,
        model_name=model_name,
        model_params_json=model_params,
        status="pending"
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
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get a specific run"""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    
    run = db.query(Run).filter(Run.id == run_uuid).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
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

# Playground endpoint (simplified for now)
@app.post("/playground/test")
def playground_test(
    prompt: str,
    model_provider: str = "openai",
    model_name: str = "gpt-3.5-turbo",
    evaluator_ids: List[str] = None
):
    """Test a single prompt (placeholder implementation)"""
    if evaluator_ids is None:
        evaluator_ids = []
    
    return {
        "output": f"Mock response to: {prompt[:50]}...",
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
            for eid in evaluator_ids[:2]  # Limit to first 2
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)