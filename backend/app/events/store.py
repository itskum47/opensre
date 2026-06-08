import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


class EventStore:
    def __init__(self, base_dir: str = "backend/data/events"):
        self.base_dir = str(Path(base_dir))
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)

    def _investigation_dir(self, investigation_id: str) -> Path:
        directory = Path(self.base_dir) / investigation_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write_event(
        self,
        investigation_id: str,
        source_type: str,
        source_id: str,
        payload: dict[str, Any],
    ) -> str:
        investigation_dir = self._investigation_dir(investigation_id)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(":", "-")
        filename = f"{timestamp}__{source_type}__{source_id}.json"
        filepath = investigation_dir / filename

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": source_type,
            "source_id": source_id,
            "payload": payload,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=2)

        return str(filepath)

    def get_events(self, investigation_id: str) -> list[dict[str, Any]]:
        investigation_dir = Path(self.base_dir) / investigation_id
        if not investigation_dir.exists():
            return []

        events: list[dict[str, Any]] = []
        for filepath in sorted(investigation_dir.glob("*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    event = json.load(f)
                if isinstance(event, dict):
                    events.append(event)
            except Exception:
                continue

        return events
