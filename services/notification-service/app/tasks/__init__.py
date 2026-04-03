"""Celery task package — exposes `celery` for `celery -A app.tasks`."""

from app.tasks.celery_app import celery_app

celery = celery_app

__all__ = ["celery", "celery_app"]
