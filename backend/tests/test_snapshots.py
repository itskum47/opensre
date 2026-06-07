import os
import json
import pytest
import shutil
from backend.app.domain.incidents.schemas import IncidentReportV1, ConfidenceFactors, EvidenceSource
from backend.app.domain.incidents.snapshots import SnapshotManager

@pytest.fixture
def temp_snapshot_manager(tmp_path):
    snap_dir = tmp_path / "snapshots"
    yield SnapshotManager(base_dir=str(snap_dir))
    if snap_dir.exists():
        shutil.rmtree(snap_dir)

def test_incident_report_validation():
    factors = ConfidenceFactors(
        temporal_alignment=90,
        evidence_strength=80,
        source_reliability=95,
        historical_similarity=70
    )
    evidence = [
        EvidenceSource(
            source_type="loki",
            source_id="redis_log",
            collected_at="2026-06-07T10:30:00Z",
            reliability_score=90
        )
    ]
    report = IncidentReportV1(
        summary="Redis saturation occurred",
        root_cause="Connection exhaustion",
        confidence=85.5,
        confidence_factors=factors,
        evidence=evidence,
        service_owners=["infra-team"]
    )
    assert report.schema_version == "1.0"
    assert report.summary == "Redis saturation occurred"
    assert report.confidence_factors.temporal_alignment == 90

def test_snapshot_write_and_load(temp_snapshot_manager):
    investigation_id = "test-snapshot-123"
    filepath = temp_snapshot_manager.write_snapshot(
        investigation_id=investigation_id,
        raw_events=[],
        timeline=[],
        graph={},
        findings=[],
        report={"summary": "test report"},
        metadata={"model": "gemini-2.5-pro", "temperature": 0.0}
    )
    assert os.path.exists(filepath)
    
    data = temp_snapshot_manager.load_snapshot(investigation_id)
    assert data["schema_version"] == "1.0"
    assert data["pipeline_version"] == "1.0"
    assert data["metadata"]["model"] == "gemini-2.5-pro"
