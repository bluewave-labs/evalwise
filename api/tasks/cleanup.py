from celery_app import celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, and_
from datetime import datetime, timedelta
import os

from models import Result, Evaluation

# Database setup for Celery tasks
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://evalwise:evalwise123@localhost:5432/evalwise")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery.task
def cleanup_old_results():
    """Clean up results older than 90 days"""
    
    db = SessionLocal()
    try:
        # Calculate cutoff date (90 days ago)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Find old results
        old_results = db.query(Result).filter(
            Result.created_at < cutoff_date
        ).all()
        
        if not old_results:
            return {
                'status': 'completed',
                'deleted_results': 0,
                'deleted_evaluations': 0,
                'message': 'No old results to clean up'
            }
        
        old_result_ids = [result.id for result in old_results]
        
        # Delete evaluations first (foreign key constraint)
        deleted_evaluations = db.query(Evaluation).filter(
            Evaluation.result_id.in_(old_result_ids)
        ).delete(synchronize_session=False)
        
        # Delete results
        deleted_results = db.query(Result).filter(
            Result.id.in_(old_result_ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            'status': 'completed',
            'deleted_results': deleted_results,
            'deleted_evaluations': deleted_evaluations,
            'cutoff_date': cutoff_date.isoformat(),
            'message': f'Successfully cleaned up {deleted_results} results and {deleted_evaluations} evaluations older than 90 days'
        }
        
    except Exception as e:
        db.rollback()
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to clean up old results'
        }
        
    finally:
        db.close()

@celery.task
def cleanup_failed_runs():
    """Clean up runs that have been stuck in 'running' status for more than 24 hours"""
    
    from models import Run
    
    db = SessionLocal()
    try:
        # Calculate cutoff date (24 hours ago)
        cutoff_date = datetime.utcnow() - timedelta(hours=24)
        
        # Find stuck runs
        stuck_runs = db.query(Run).filter(
            and_(
                Run.status == "running",
                Run.started_at < cutoff_date
            )
        ).all()
        
        if not stuck_runs:
            return {
                'status': 'completed',
                'updated_runs': 0,
                'message': 'No stuck runs to clean up'
            }
        
        # Mark stuck runs as failed
        updated_count = 0
        for run in stuck_runs:
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            updated_count += 1
        
        db.commit()
        
        return {
            'status': 'completed',
            'updated_runs': updated_count,
            'cutoff_date': cutoff_date.isoformat(),
            'message': f'Successfully marked {updated_count} stuck runs as failed'
        }
        
    except Exception as e:
        db.rollback()
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Failed to clean up stuck runs'
        }
        
    finally:
        db.close()

@celery.task
def get_cleanup_stats():
    """Get statistics about data that can be cleaned up"""
    
    from models import Run
    
    db = SessionLocal()
    try:
        # Results older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_results_count = db.query(Result).filter(
            Result.created_at < cutoff_date
        ).count()
        
        # Stuck runs
        stuck_cutoff = datetime.utcnow() - timedelta(hours=24)
        stuck_runs_count = db.query(Run).filter(
            and_(
                Run.status == "running",
                Run.started_at < stuck_cutoff
            )
        ).count()
        
        # Total counts
        total_results = db.query(Result).count()
        total_runs = db.query(Run).count()
        
        return {
            'old_results_count': old_results_count,
            'stuck_runs_count': stuck_runs_count,
            'total_results': total_results,
            'total_runs': total_runs,
            'retention_days': 90,
            'stuck_threshold_hours': 24
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Failed to get cleanup stats'
        }
        
    finally:
        db.close()