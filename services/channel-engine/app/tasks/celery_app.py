"""Celery application for channel-engine."""
from celery import Celery

from app.config import settings

celery_app = Celery(
    "kira-channel-engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.ari_push",
        "app.tasks.booking_pull",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Celery beat schedule: pull bookings from all active channels every 60 seconds
celery_app.conf.beat_schedule = {
    "booking-pull-all-channels": {
        "task": "app.tasks.booking_pull.pull_bookings_all_channels",
        "schedule": settings.booking_pull_interval,
    },
}
