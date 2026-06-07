from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import engine, Base, get_db
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.snapshots import SnapshotManager
from backend.app.workers.tasks import run_investigation_task
import uuid

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenSRE API", version="1.0")

@app.post("/investigations", status_code=status.HTTP_201_CREATED)
def trigger_investigation(db: Session = Depends(get_db)):
    """Triggers an asynchronous investigation pipeline execution."""
    investigation_id = str(uuid.uuid4())
    
    # Register investigation in database
    investigation = Investigation(id=investigation_id, status=InvestigationStatus.QUEUED)
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    
    # Enqueue in Celery worker queue
    run_investigation_task.delay(investigation_id)
    
    return {"job_id": investigation_id}

@app.get("/investigations/{investigation_id}")
def get_investigation_status(investigation_id: str, db: Session = Depends(get_db)):
    """Returns the current registry status of an investigation."""
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "id": investigation.id,
        "status": investigation.status.value,
        "started_at": investigation.started_at.isoformat(),
        "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None,
        "duration": investigation.duration,
        "pipeline_version": investigation.pipeline_version,
        "report_id": investigation.report_id
    }

@app.get("/investigations/{investigation_id}/snapshot")
def get_investigation_snapshot(investigation_id: str):
    """Retrieves the finished snapshot representation for an investigation."""
    manager = SnapshotManager()
    try:
        return manager.load_snapshot(investigation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Snapshot not found for this investigation")
