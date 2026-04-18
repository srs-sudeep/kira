"""Celery application for the rate-inventory-service."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "kira-rate-inventory",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.seasonal_apply"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        # Nightly at 01:00 UTC — apply seasonal pricing rules across all tenants
        "nightly-seasonal-apply": {
            "task": "app.tasks.seasonal_apply.apply_seasonal_rules_all_tenants",
            "schedule": crontab(hour=1, minute=0),
        },
    },
)
