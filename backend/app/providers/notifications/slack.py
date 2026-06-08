import logging
from typing import Dict, Any, List
from slack_sdk import WebClient
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class SlackProvider:
    def __init__(self):
        self.token = settings.SLACK_BOT_TOKEN
        self.channel = settings.SLACK_CHANNEL
        self.client = None
        if self.token and self.token != "mock-token":
            self.client = WebClient(token=self.token)

    def send_alert(self, text: str, blocks: List[Dict[str, Any]] = None) -> bool:
        if not settings.ENABLE_SLACK:
            logger.debug("Slack notifications disabled via feature flag.")
            return False

        if not self.client:
            logger.warning(f"Slack client offline (mock-token). Alert payload: {text}")
            return False

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text=text,
                blocks=blocks
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to deliver Slack notification: {e}")
            return False

    def build_investigation_blocks(self, investigation_id: str, status: str, details: str) -> List[Dict[str, Any]]:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*OpenSRE Investigation Update: {investigation_id}*\n*Status:* `{status}`\n*Details:* {details}"
                }
            }
        ]
        
        # If a remediation plan is proposed, add interactive approval buttons
        if status == "REMEDIATION_PROPOSED":
            blocks.append({
                "type": "actions",
                "block_id": f"remediation_{investigation_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve ✅"},
                        "style": "primary",
                        "action_id": "approve_remediation",
                        "value": investigation_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject ❌"},
                        "style": "danger",
                        "action_id": "reject_remediation",
                        "value": investigation_id
                    }
                ]
            })
            
        return blocks
