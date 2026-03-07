from celery import Celery

from app.config import settings

celery_app = Celery(
    "arterial",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.beat_schedule = {
    # Example: scheduled ingestion
    # "refresh-toronto-parcels": {
    #     "task": "app.tasks.ingestion.refresh_source",
    #     "schedule": crontab(hour=2, minute=0),
    #     "args": ("toronto-parcels",),
    # },
}
