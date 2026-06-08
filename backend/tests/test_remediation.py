import pytest
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
import backend.app.database
import backend.app.workers.tasks
import backend.app.main

from backend.app.domain.incidents.models import RemediationAction, RemediationStatus, Investigation, InvestigationStatus
from backend.app.domain.audit.models import AuditRecord
from backend.app.domain.remediation.runner import RemediationRunner
from backend.app.workers.tasks import run_remediation_task
from backend.app.main import app

DB_FILE = "./test_remediation.db"

@pytest.fixture(autouse=True)
def patch_session_local():
    # Remove any existing stale DB file
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

    engine = create_engine(f"sqlite:///{DB_FILE}", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(bind=engine)
    
    # Save original references
    orig_engine = backend.app.database.engine
    orig_session_local = backend.app.database.SessionLocal
    
    # Override engine and SessionLocal in all modules
    backend.app.database.engine = engine
    backend.app.database.SessionLocal = TestSessionLocal
    backend.app.workers.tasks.SessionLocal = TestSessionLocal
    
    # Re-create all tables
    Base.metadata.create_all(bind=engine)
    
    yield TestSessionLocal
    
    # Restore original references
    backend.app.database.engine = orig_engine
    backend.app.database.SessionLocal = orig_session_local
    backend.app.workers.tasks.SessionLocal = orig_session_local
    
    # Clean up DB file
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

@pytest.fixture
def db_session(patch_session_local):
    session = patch_session_local()
    yield session
    session.close()

@pytest.fixture
def client(patch_session_local):
    def override_get_db():
        db = patch_session_local()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_remediation_runner_cooldown(db_session):
    runner = RemediationRunner(db_session)
    
    # 1. Initially, no actions run, so cooldown allows execution
    assert runner.check_cooldown("restart_pod", "auth-service") is True

    # 2. Add an executing action
    act1 = RemediationAction(
        id="remed-1",
        investigation_id="inv-1",
        status=RemediationStatus.EXECUTING,
        action_name="restart_pod",
        target_resource="auth-service",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(act1)
    db_session.commit()

    # Cooldown should now block a new action on same target
    assert runner.check_cooldown("restart_pod", "auth-service") is False

    # Check cooldown with exclude_id equal to the active action should bypass
    assert runner.check_cooldown("restart_pod", "auth-service", exclude_id="remed-1") is True

    # Cooldown for different action on same resource, or same action on different resource is allowed
    assert runner.check_cooldown("rollback", "auth-service") is True
    assert runner.check_cooldown("restart_pod", "db-service") is True

    # Cooldown after window expires (e.g. 10 minutes ago)
    act1.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()
    assert runner.check_cooldown("restart_pod", "auth-service") is True

@patch("backend.app.workers.tasks.run_remediation_task.delay")
def test_endpoints_approve_reject(mock_delay, client, db_session):
    # Setup pending remediation action
    act = RemediationAction(
        id="remed-test-endpoints",
        investigation_id="inv-test-endpoints",
        status=RemediationStatus.PENDING_APPROVAL,
        action_name="restart",
        target_resource="auth-service",
        params=json.dumps({"replicas": 3})
    )
    db_session.add(act)
    db_session.commit()

    # Test status lookup
    response = client.get("/api/v1/remediations/remed-test-endpoints")
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_APPROVAL"
    assert response.json()["params"] == {"replicas": 3}

    # Test approve endpoint
    response = client.post("/api/v1/remediations/remed-test-endpoints/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    
    db_session.refresh(act)
    assert act.status == RemediationStatus.APPROVED
    mock_delay.assert_called_once_with("remed-test-endpoints")

    # Reject endpoint validation fails if not PENDING_APPROVAL
    response = client.post("/api/v1/remediations/remed-test-endpoints/reject")
    assert response.status_code == 400

@patch("backend.app.workers.tasks.run_remediation_task.delay")
def test_slack_webhook_actions(mock_delay, client, db_session):
    # Setup pending action
    act = RemediationAction(
        id="remed-slack",
        investigation_id="inv-slack-123",
        status=RemediationStatus.PENDING_APPROVAL,
        action_name="rollback",
        target_resource="payment-service"
    )
    db_session.add(act)
    db_session.commit()

    # Form payload mimicking Slack button click
    slack_payload = {
        "actions": [
            {
                "action_id": "approve_remediation",
                "value": "inv-slack-123"
            }
        ]
    }

    # Post with X-Mock-Slack bypass header to skip HMAC signature check
    response = client.post(
        "/api/v1/slack/actions",
        data={"payload": json.dumps(slack_payload)},
        headers={"X-Mock-Slack": "true"}
    )
    assert response.status_code == 200
    assert "Approved" in response.json()["text"]

    db_session.refresh(act)
    assert act.status == RemediationStatus.APPROVED
    mock_delay.assert_called_once_with("remed-slack")

def test_celery_task_execution(db_session):
    # Setup APPROVED remediation action
    act = RemediationAction(
        id="remed-celery-1",
        investigation_id="inv-celery-1",
        status=RemediationStatus.APPROVED,
        action_name="restart",
        target_resource="cache-service"
    )
    db_session.add(act)
    db_session.commit()

    # Execute task synchronously
    success = run_remediation_task("remed-celery-1")
    assert success is True

    db_session.refresh(act)
    assert act.status == RemediationStatus.COMPLETED

    # Check audits
    audits = db_session.query(AuditRecord).filter(AuditRecord.investigation_id == "inv-celery-1").all()
    actions = [a.action for a in audits]
    assert "remediation_started" in actions
    assert "remediation_finished" in actions

def test_celery_task_validation_failure(db_session):
    # Setup APPROVED remediation action on a resource that triggers health failure in tests
    act = RemediationAction(
        id="remed-celery-fail",
        investigation_id="inv-celery-fail",
        status=RemediationStatus.APPROVED,
        action_name="restart",
        target_resource="fail-health-service"
    )
    db_session.add(act)
    db_session.commit()

    # Execute task
    success = run_remediation_task("remed-celery-fail")
    assert success is False

    db_session.refresh(act)
    assert act.status == RemediationStatus.FAILED
