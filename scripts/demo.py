#!/usr/bin/env python3
"""
Demo script that runs the seeded dataset through evaluators to showcase the system
"""

import sys
import os
import time
import json

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/api")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Dataset, Scenario, Evaluator, Run
from database import DATABASE_URL

def create_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def run_demo():
    """Run demo evaluation"""
    print("Starting EvalWise demo...")
    
    db = create_session()
    try:
        # Get demo dataset
        dataset = db.query(Dataset).filter(Dataset.name == "Demo QA Dataset").first()
        if not dataset:
            print("Demo dataset not found. Please run 'make seed' first.")
            return 1
        
        # Get some scenarios
        jailbreak_scenario = db.query(Scenario).filter(Scenario.type == "jailbreak_basic").first()
        safety_scenario = db.query(Scenario).filter(Scenario.type == "safety_probe").first()
        
        if not jailbreak_scenario or not safety_scenario:
            print("Demo scenarios not found. Please run 'make seed' first.")
            return 1
        
        # Get evaluators
        evaluators = db.query(Evaluator).all()
        if not evaluators:
            print("Demo evaluators not found. Please run 'make seed' first.")
            return 1
        
        print(f"Found dataset: {dataset.name} with {len(dataset.items)} items")
        print(f"Using scenarios: {jailbreak_scenario.name}, {safety_scenario.name}")
        print(f"Using {len(evaluators)} evaluators")
        
        # Create demo run
        demo_run = Run(
            name="Demo Run - Safety Testing",
            dataset_id=dataset.id,
            dataset_version_hash=dataset.version_hash,
            scenario_ids=[str(jailbreak_scenario.id), str(safety_scenario.id)],
            model_provider="openai",
            model_name="gpt-3.5-turbo",
            model_params_json={"temperature": 0.7, "max_tokens": 500},
            status="pending"
        )
        db.add(demo_run)
        db.commit()
        db.refresh(demo_run)
        
        print(f"\nCreated demo run: {demo_run.id}")
        print("To start processing:")
        print(f"1. Make sure OpenAI API key is set in .env file")
        print(f"2. Visit http://localhost:3000 to see the web interface")
        print(f"3. The run will be processed automatically by Celery workers")
        print(f"\nRun ID: {demo_run.id}")
        print(f"API endpoint: http://localhost:8000/runs/{demo_run.id}")
        
        # Show what the demo will test
        print(f"\nDemo will test {len(dataset.items)} questions including:")
        high_risk_items = [item for item in dataset.items 
                          if item.metadata_json.get("difficulty") == "high_risk"]
        print(f"- {len(high_risk_items)} high-risk safety test cases")
        
        safety_categories = set()
        for item in dataset.items:
            if item.metadata_json.get("category"):
                safety_categories.add(item.metadata_json["category"])
        
        print(f"- Categories: {', '.join(safety_categories)}")
        print(f"- Each item will be tested with 2 scenarios (jailbreak + safety probe)")
        print(f"- Each result evaluated by {len(evaluators)} evaluators")
        print(f"- Total evaluations: {len(dataset.items)} × 2 × {len(evaluators)} = {len(dataset.items) * 2 * len(evaluators)}")
        
        return 0
        
    except Exception as e:
        print(f"Error running demo: {str(e)}")
        return 1
    
    finally:
        db.close()

def main():
    """Main demo function"""
    return run_demo()

if __name__ == "__main__":
    exit(main())