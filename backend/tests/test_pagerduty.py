import pytest
from unittest.mock import MagicMock, patch
from backend.app.providers.notifications.pagerduty import PagerDutyProvider
from backend.app.providers.notifications.router import NotificationRouter
from backend.app.config.settings import settings

def test_pagerduty_provider_mock():
    provider = PagerDutyProvider()
    
    # Mock _send_request method
    provider._send_request = MagicMock(return_value=True)
    
    assert provider.acknowledge_incident("pd-123") is True
    provider._send_request.assert_called_with(
        "PUT",
        "https://api.pagerduty.com/incidents/pd-123",
        {"incident": {"type": "incident_reference", "status": "acknowledged"}}
    )

    assert provider.resolve_incident("pd-123") is True
    provider._send_request.assert_called_with(
        "PUT",
        "https://api.pagerduty.com/incidents/pd-123",
        {"incident": {"type": "incident_reference", "status": "resolved"}}
    )

    assert provider.add_note("pd-123", "Some notes") is True
    provider._send_request.assert_called_with(
        "POST",
        "https://api.pagerduty.com/incidents/pd-123/notes",
        {"note": {"content": "Some notes"}}
    )

def test_notification_router_dispatch():
    router = NotificationRouter()
    router.slack = MagicMock()
    router.pagerduty = MagicMock()

    payload = {
        "investigation_id": "test-id",
        "status": "COLLECTING",
        "details": "Collecting data...",
        "pagerduty_incident_id": "pd-123"
    }

    # Test started dispatch
    router.dispatch("investigation_started", payload)
    assert router.slack.send_alert.called
    assert router.pagerduty.acknowledge_incident.called
    assert router.pagerduty.add_note.called

    # Reset mocks
    router.slack.reset_mock()
    router.pagerduty.reset_mock()

    # Test transition dispatch
    router.dispatch("stage_transition", payload)
    assert router.slack.send_alert.called
    assert not router.pagerduty.acknowledge_incident.called

    # Reset mocks
    router.slack.reset_mock()
    router.pagerduty.reset_mock()

    # Test completed dispatch
    router.dispatch("investigation_completed", payload)
    assert router.slack.send_alert.called
    assert router.pagerduty.resolve_incident.called
    assert router.pagerduty.add_note.called
