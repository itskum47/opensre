import os
import json
from typing import Dict, Any, List

class SnapshotManager:
    def __init__(self, base_dir: str = "backend/app/snapshots"):
        self.base_dir = os.path.abspath(base_dir)

    def write_snapshot(
        self,
        investigation_id: str,
        raw_events: List[Dict[str, Any]],
        timeline: List[Dict[str, Any]],
        graph: Dict[str, Any],
        findings: List[Dict[str, Any]],
        report: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Saves a unified snapshot of the completed investigation."""
        os.makedirs(self.base_dir, exist_ok=True)
        filepath = os.path.join(self.base_dir, f"{investigation_id}_snapshot.json")

        snapshot_data = {
            "schema_version": "1.0",
            "pipeline_version": "1.0",
            "ranking_version": "1.0",
            "graph_version": "1.0",
            "prompt_version": "1.0",
            "investigation_id": investigation_id,
            "raw_events": raw_events,
            "timeline": timeline,
            "graph": graph,
            "findings": findings,
            "report": report,
            "metadata": metadata
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2)

        return filepath

    def load_snapshot(self, investigation_id: str) -> Dict[str, Any]:
        """Loads a snapshot for a given investigation_id."""
        filepath = os.path.join(self.base_dir, f"{investigation_id}_snapshot.json")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Snapshot not found for investigation {investigation_id}")

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
