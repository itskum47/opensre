import pytest
from backend.app.workers.tasks import celery_app, run_investigation_task

def test_celery_config():
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.timezone == "UTC"
