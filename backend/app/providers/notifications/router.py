import logging
from typing import Dict, Any
from backend.app.providers.notifications.slack import SlackProvider
from backend.app.providers.notifications.pagerduty import PagerDutyProvider

logger = logging.getLogger(__name__)

class NotificationRouter:
    def __init__(self):
        self.slack = SlackProvider()
        self.pagerduty = PagerDutyProvider()

    def dispatch(self, event_type: str, payload: Dict[str, Any]):
        investigation_id = payload.get("investigation_id")
        status = payload.get("status")
        details = payload.get("details", "")
        pd_incident_id = payload.get("pagerduty_incident_id")

        logger.info(f"Dispatching notification event '{event_type}' for {investigation_id}")

        if event_type == "investigation_started":
            # 1. Slack notification
            text = f"🚨 *OpenSRE Investigation Started: {investigation_id}*"
            blocks = self.slack.build_investigation_blocks(investigation_id, status, details)
            self.slack.send_alert(text, blocks)

            # 2. PagerDuty Acknowledge
            if pd_incident_id:
                self.pagerduty.acknowledge_incident(pd_incident_id)
                self.pagerduty.add_note(pd_incident_id, f"OpenSRE investigation {investigation_id} has started.")

        elif event_type == "stage_transition":
            text = f"🔄 *OpenSRE Transition:* Investigation {investigation_id} entered state `{status}`: {details}"
            self.slack.send_alert(text)

        elif event_type == "investigation_completed":
            # 1. Slack summary notification
            text = f"✅ *OpenSRE Investigation Completed: {investigation_id}*"
            blocks = self.slack.build_investigation_blocks(investigation_id, status, details)
            self.slack.send_alert(text, blocks)

            # 2. PagerDuty Resolve & Note attachment
            if pd_incident_id:
                self.pagerduty.add_note(pd_incident_id, f"OpenSRE investigation complete.\nRoot Cause Findings:\n{details}")
                self.pagerduty.resolve_incident(pd_incident_id)
