from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery("localops-worker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_track_started=True, task_serializer="json", accept_content=["json"], result_serializer="json")

celery_app.autodiscover_tasks(["worker.runner"])
