from worker.celery_app import celery_app


def test_celery_app_name() -> None:
    assert celery_app.main == "localops-worker"
