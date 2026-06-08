import logging
from typing import Dict, Any
import httpx
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class PagerDutyProvider:
    def __init__(self):
        self.api_key = settings.PAGERDUTY_API_KEY
        self.headers = {
            "Authorization": f"Token token={self.api_key}",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Content-Type": "application/json",
            "From": "admin@opensre.io"
        }

    def _send_request(self, method: str, url: str, json_data: Dict[str, Any] = None) -> bool:
        if not settings.ENABLE_PAGERDUTY:
            logger.debug("PagerDuty integration disabled via feature flag.")
            return False

        if not self.api_key or self.api_key == "mock-key":
            logger.warning(f"PagerDuty client offline (mock API key). Request: {method} {url} Payload: {json_data}")
            return False

        try:
            with httpx.Client() as client:
                response = client.request(method, url, headers=self.headers, json=json_data)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(f"PagerDuty API call failed: {e}")
            return False

    def acknowledge_incident(self, incident_id: str) -> bool:
        url = f"https://api.pagerduty.com/incidents/{incident_id}"
        payload = {
            "incident": {
                "type": "incident_reference",
                "status": "acknowledged"
            }
        }
        return self._send_request("PUT", url, payload)

    def resolve_incident(self, incident_id: str) -> bool:
        url = f"https://api.pagerduty.com/incidents/{incident_id}"
        payload = {
            "incident": {
                "type": "incident_reference",
                "status": "resolved"
            }
        }
        return self._send_request("PUT", url, payload)

    def add_note(self, incident_id: str, content: str) -> bool:
        url = f"https://api.pagerduty.com/incidents/{incident_id}/notes"
        payload = {
            "note": {
                "content": content
            }
        }
        return self._send_request("POST", url, payload)
