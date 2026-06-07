import asyncio
import logging
from celery import Celery
from backend.app.config.settings import settings
from backend.app.database import SessionLocal
from backend.app.domain.incidents.pipeline import InvestigationPipeline

logger = logging.getLogger(__name__)

celery_app = Celery("opensre")
celery_app.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL.replace("/0", "/1"), # Keep result backend on DB 1
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True
)

@celery_app.task(name="backend.app.workers.tasks.run_investigation_task")
def run_investigation_task(investigation_id: str):
    """Celery worker task runner executing the InvestigationPipeline synchronously."""
    logger.info(f"Worker enqueued run for investigation: {investigation_id}")
    db = SessionLocal()
    try:
        pipeline = InvestigationPipeline(db)
        # Run the async pipeline in the worker's synchronous thread block
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(pipeline.execute(investigation_id))
    except Exception as e:
        logger.error(f"Worker task failed for investigation {investigation_id}: {e}")
        raise e
    finally:
        db.close()
