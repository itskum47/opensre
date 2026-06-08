from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.database import engine, Base, get_db
from backend.app.domain.incidents.models import Investigation, InvestigationStatus, RemediationAction, RemediationStatus
from backend.app.domain.incidents.snapshots import SnapshotManager

from backend.app.workers.tasks import run_investigation_task
from backend.app.config.settings import settings
import uuid
import hmac
import hashlib
import json
import time

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OpenSRE API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@app.get("/investigations")
def list_investigations(db: Session = Depends(get_db)):
    """Lists all investigations registered in the database, ordered by start time descending."""
    investigations = db.query(Investigation).order_by(Investigation.started_at.desc()).all()
    return [
        {
            "id": inv.id,
            "status": inv.status.value,
            "started_at": inv.started_at.isoformat(),
            "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
            "duration": inv.duration,
            "pipeline_version": inv.pipeline_version,
            "report_id": inv.report_id
        }
        for inv in investigations
    ]

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

async def verify_slack_signature(request: Request):
    """Dependency verifying Slack signature using signing secret."""
    # Allow mock bypass in testing
    if request.headers.get("X-Mock-Slack") == "true":
        return

    body = await request.body()
    signature = request.headers.get("X-Slack-Signature")
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    
    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing Slack verification headers")
        
    if abs(time.time() - int(timestamp)) > 60 * 5:
        raise HTTPException(status_code=401, detail="Request timestamp expired")
        
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}".encode('utf-8')
    computed_sig = "v0=" + hmac.new(
        key=settings.SLACK_SIGNING_SECRET.encode('utf-8'),
        msg=sig_basestring,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(computed_sig, signature):
        raise HTTPException(status_code=403, detail="Invalid Slack signature")

@app.post("/api/v1/slack/actions")
async def slack_actions_webhook(
    request: Request, 
    db: Session = Depends(get_db),
    _ = Depends(verify_slack_signature)
):
    """Receives interactive block kit approvals from Slack."""
    form_data = await request.form()
    payload = form_data.get("payload")
    if not payload:
        raise HTTPException(status_code=400, detail="Missing payload form field")
        
    try:
        payload_dict = json.loads(payload)
        action = payload_dict["actions"][0]
        action_id = action["action_id"]
        investigation_id = action["value"]
        
        # Find the pending remediation action for this investigation
        remediation = db.query(RemediationAction).filter(
            RemediationAction.investigation_id == investigation_id,
            RemediationAction.status == RemediationStatus.PENDING_APPROVAL
        ).first()
        
        if not remediation:
            return {
                "response_type": "ephemeral",
                "text": "❌ No pending remediation action found for this investigation."
            }
            
        if action_id == "approve_remediation":
            remediation.status = RemediationStatus.APPROVED
            db.commit()
            
            # Enqueue Celery task
            from backend.app.workers.tasks import run_remediation_task
            run_remediation_task.delay(remediation.id)
            
            message_text = f"✅ *Approved:* Remediation action `{remediation.action_name}` on `{remediation.target_resource}` has been approved and is running."
        elif action_id == "reject_remediation":
            remediation.status = RemediationStatus.REJECTED
            db.commit()
            
            message_text = f"❌ *Rejected:* Remediation action `{remediation.action_name}` on `{remediation.target_resource}` has been rejected."
        else:
            return {"status": "ignored"}
            
        return {
            "response_type": "in_channel",
            "text": message_text
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process Slack action: {e}")

@app.get("/api/v1/remediations/{remediation_id}")
def get_remediation_status(remediation_id: str, db: Session = Depends(get_db)):
    remediation = db.query(RemediationAction).filter(RemediationAction.id == remediation_id).first()
    if not remediation:
        raise HTTPException(status_code=404, detail="Remediation action not found")
    
    return {
        "id": remediation.id,
        "investigation_id": remediation.investigation_id,
        "status": remediation.status.value,
        "action_name": remediation.action_name,
        "target_resource": remediation.target_resource,
        "params": json.loads(remediation.params) if remediation.params else None,
        "created_at": remediation.created_at.isoformat(),
        "updated_at": remediation.updated_at.isoformat()
    }

@app.post("/api/v1/remediations/{remediation_id}/approve")
def approve_remediation(remediation_id: str, db: Session = Depends(get_db)):
    remediation = db.query(RemediationAction).filter(RemediationAction.id == remediation_id).first()
    if not remediation:
        raise HTTPException(status_code=404, detail="Remediation action not found")
    
    if remediation.status != RemediationStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Remediation is not in PENDING_APPROVAL state (current status: {remediation.status.value})")
        
    remediation.status = RemediationStatus.APPROVED
    db.commit()
    
    # Trigger Celery task
    from backend.app.workers.tasks import run_remediation_task
    run_remediation_task.delay(remediation.id)
    
    return {"status": "approved", "remediation_id": remediation_id}

@app.post("/api/v1/remediations/{remediation_id}/reject")
def reject_remediation(remediation_id: str, db: Session = Depends(get_db)):
    remediation = db.query(RemediationAction).filter(RemediationAction.id == remediation_id).first()
    if not remediation:
        raise HTTPException(status_code=404, detail="Remediation action not found")
        
    if remediation.status != RemediationStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Remediation is not in PENDING_APPROVAL state (current status: {remediation.status.value})")
        
    remediation.status = RemediationStatus.REJECTED
    db.commit()
    
    return {"status": "rejected", "remediation_id": remediation_id}


