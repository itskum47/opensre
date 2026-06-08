import pytest
import hmac
import hashlib
import json
import time
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.app.main import app
from backend.app.providers.notifications.slack import SlackProvider
from backend.app.config.settings import settings

client = TestClient(app)

def test_slack_provider_block_kit():
    provider = SlackProvider()
    blocks = provider.build_investigation_blocks(
        investigation_id="test-id",
        status="REMEDIATION_PROPOSED",
        details="Redis CPU high"
    )
    
    assert len(blocks) == 2
    assert blocks[0]["type"] == "section"
    assert "test-id" in blocks[0]["text"]["text"]
    assert blocks[1]["type"] == "actions"
    assert blocks[1]["elements"][0]["action_id"] == "approve_remediation"

@patch("backend.app.workers.tasks.run_remediation_task.delay")
def test_slack_webhook_signature_verification(mock_delay):
    from backend.app.database import get_db
    
    mock_db = MagicMock()
    mock_remediation = MagicMock()
    mock_remediation.id = "remed-slack"
    mock_remediation.investigation_id = "test-id"
    mock_remediation.status = "PENDING_APPROVAL"
    mock_remediation.action_name = "rollback"
    mock_remediation.target_resource = "payment-service"
    
    # Mock db.query(RemediationAction).filter(...).first()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_remediation
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    try:
        # 1. Invalid signature should return 403
        headers = {
            "X-Slack-Signature": "v0=invalid-sig",
            "X-Slack-Request-Timestamp": str(int(time.time()))
        }
        payload = {"payload": json.dumps({"actions": [{"action_id": "approve_remediation", "value": "test-id"}]})}
        response = client.post("/api/v1/slack/actions", data=payload, headers=headers)
        assert response.status_code == 403
        assert "Invalid Slack signature" in response.json()["detail"]
    
        # 2. Mock header should bypass and succeed
        mock_headers = {
            "X-Mock-Slack": "true"
        }
        response = client.post("/api/v1/slack/actions", data=payload, headers=mock_headers)
        assert response.status_code == 200
        assert response.json()["response_type"] == "in_channel"
        assert "Approved" in response.json()["text"]
        mock_delay.assert_called_once_with("remed-slack")
    finally:
        app.dependency_overrides.clear()

