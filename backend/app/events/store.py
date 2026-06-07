import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

class EventStore:
    def __init__(self, base_dir: str = "backend/app/events"):
        self.base_dir = os.path.abspath(base_dir)

    def write_event(self, investigation_id: str, source_type: str, source_id: str, payload: Dict[str, Any]) -> str:
        """Writes a raw evidence event payload to an immutable file under base_dir."""
        # Ensure directory for this investigation exists
        investigation_dir = os.path.join(self.base_dir, investigation_id)
        os.makedirs(investigation_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{source_type}_{source_id}_{timestamp}.json"
        filepath = os.path.join(investigation_dir, filename)

        # Enforce write-once (fail if file somehow exists)
        if os.path.exists(filepath):
            raise FileExistsError(f"Event file {filepath} already exists and cannot be overwritten")

        event_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": source_type,
            "source_id": source_id,
            "payload": payload
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(event_data, f, indent=2)

        return filepath

    def get_events(self, investigation_id: str) -> List[Dict[str, Any]]:
        """Retrieves all events for a given investigation_id."""
        investigation_dir = os.path.join(self.base_dir, investigation_id)
        if not os.path.exists(investigation_dir):
            return []

        events = []
        for filename in sorted(os.listdir(investigation_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(investigation_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        events.append(json.load(f))
                except Exception:
                    # Ignore malformed files or permission errors
                    continue
        return events
