from celery import Celery
from config import settings

# Create Celery app
celery = Celery(
    "evalwise",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tasks.evaluation", "tasks.cleanup", "tasks.simple_evaluation"]
)

# Celery configuration
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "tasks.evaluation.*": {"queue": "evaluation"},
        "tasks.cleanup.*": {"queue": "cleanup"},
    },
    beat_schedule={
        "cleanup-old-results": {
            "task": "tasks.cleanup.cleanup_old_results",
            "schedule": 86400.0,  # Run daily (24 hours)
        },
    },
)