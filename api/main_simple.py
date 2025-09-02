from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os

# Import database and models
from database import get_db, engine
from models import Base, Dataset, Scenario, Evaluator

app = FastAPI(title="EvalWise API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "EvalWise API is running"}

@app.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    """List all datasets"""
    datasets = db.query(Dataset).all()
    return [
        {
            "id": str(dataset.id),
            "name": dataset.name,
            "version_hash": dataset.version_hash,
            "tags": dataset.tags or [],
            "is_synthetic": dataset.is_synthetic,
            "created_at": dataset.created_at.isoformat()
        }
        for dataset in datasets
    ]

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)