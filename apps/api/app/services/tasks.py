from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_client = Celery("localops-api", broker=settings.redis_url, backend=settings.redis_url)
