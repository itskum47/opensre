import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class EventStore:
    def __init__(self, base_dir: str = "backend/data/events"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _investigation_dir(self, investigation_id: str) -> Path:
        directory = self.base_dir / investigation_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def write_event(
        self,
        investigation_id: str,
        source_type: str,
        source_id: str,
        payload: dict[str, Any],
    ) -> str:
        """Persist a single source payload as an immutable event JSON file."""
        investigation_dir = self._investigation_dir(investigation_id)
        now_utc = datetime.now(timezone.utc)
        timestamp = now_utc.strftime("%Y%m%dT%H%M%S%f")
        filename = f"{timestamp}__{uuid4().hex}__{source_type}__{source_id}.json"
        filepath = investigation_dir / filename
        temp_filepath = filepath.with_suffix(".tmp")

        event = {
            "timestamp": now_utc.isoformat(),
            "source_type": source_type,
            "source_id": source_id,
            "payload": payload,
        }

        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=2)
        temp_filepath.replace(filepath)

        return str(filepath)

    def get_events(self, investigation_id: str) -> list[dict[str, Any]]:
        """Load all persisted events for an investigation in filename order."""
        investigation_dir = self.base_dir / investigation_id
        if not investigation_dir.exists():
            return []

        events: list[dict[str, Any]] = []
        for filepath in sorted(investigation_dir.glob("*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    event = json.load(f)
                if isinstance(event, dict):
                    events.append(event)
            except (OSError, json.JSONDecodeError) as err:
                logger.warning("Skipping unreadable event file %s: %s", filepath, err)
                continue

        return events
