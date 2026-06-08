import asyncio
import json
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

@celery_app.task(name="backend.app.workers.tasks.run_remediation_task")
def run_remediation_task(remediation_id: str):
    """Celery task executing the approved remediation action asynchronously."""
    logger.info(f"Worker task started for remediation: {remediation_id}")
    db = SessionLocal()
    try:
        from backend.app.domain.incidents.models import RemediationAction, RemediationStatus
        from backend.app.domain.remediation.runner import RemediationRunner
        from backend.app.domain.audit.models import AuditRecord
        
        remediation = db.query(RemediationAction).filter(RemediationAction.id == remediation_id).first()
        if not remediation:
            logger.error(f"Remediation action {remediation_id} not found in database.")
            return False

        # If it was already processed, skip
        if remediation.status in (RemediationStatus.EXECUTING, RemediationStatus.COMPLETED, RemediationStatus.FAILED):
            logger.warning(f"Remediation action {remediation_id} already in state: {remediation.status.value}")
            return True

        runner = RemediationRunner(db)
        
        # 1. Cooldown Check
        if not runner.check_cooldown(remediation.action_name, remediation.target_resource, exclude_id=remediation.id):
            remediation.status = RemediationStatus.FAILED
            db.commit()
            
            # Write to Audit Trail
            audit = AuditRecord(
                action="remediation_cooldown_blocked",
                investigation_id=remediation.investigation_id,
                payload={"remediation_id": remediation_id, "reason": "cooldown active"}
            )
            db.add(audit)
            db.commit()
            
            logger.warning(f"Remediation task {remediation_id} blocked by cooldown.")
            return False

        # 2. Transition to EXECUTING
        remediation.status = RemediationStatus.EXECUTING
        db.commit()
        
        # Write to Audit Trail
        audit = AuditRecord(
            action="remediation_started",
            investigation_id=remediation.investigation_id,
            payload={"remediation_id": remediation_id, "action_name": remediation.action_name}
        )
        db.add(audit)
        db.commit()

        # 3. Execute
        params_dict = json.loads(remediation.params) if remediation.params else {}
        success = runner.execute_action(remediation.action_name, remediation.target_resource, params_dict)
        
        # 4. Post-Execution Validation Health Check
        if success:
            logger.info("Remediation command succeeded. Running validation health check...")
            healthy = runner.validate_health(remediation.target_resource)
            if healthy:
                remediation.status = RemediationStatus.COMPLETED
                logger.info(f"Remediation {remediation_id} completed and validated healthy.")
            else:
                remediation.status = RemediationStatus.FAILED
                logger.warning(f"Remediation {remediation_id} completed but failed post-remediation health check.")
        else:
            remediation.status = RemediationStatus.FAILED
            logger.warning(f"Remediation {remediation_id} failed command execution.")

        db.commit()
        
        # Write to Audit Trail
        audit = AuditRecord(
            action="remediation_finished",
            investigation_id=remediation.investigation_id,
            payload={"remediation_id": remediation_id, "status": remediation.status.value}
        )
        db.add(audit)
        db.commit()
        
        return remediation.status == RemediationStatus.COMPLETED

    except Exception as e:
        logger.error(f"Worker task failed for remediation {remediation_id}: {e}")
        try:
            remediation = db.query(RemediationAction).filter(RemediationAction.id == remediation_id).first()
            if remediation:
                remediation.status = RemediationStatus.FAILED
                db.commit()
        except Exception:
            pass
        raise e
    finally:
        db.close()

