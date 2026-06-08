import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.audit.models import AuditRecord
from backend.app.domain.incidents.models import HistoricalIncident
from backend.app.domain.incidents.memory import (
    IncidentMemoryEngine,
    extract_features_from_report,
    jaccard_similarity
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session
    session.close()

def test_jaccard_similarity():
    # Test identical sets
    assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
    # Test completely disjoint sets
    assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0
    # Test partial overlap
    assert jaccard_similarity({"a", "b"}, {"b", "c"}) == pytest.approx(1/3)  # Intersection: {"b"} (size 1), Union: {"a", "b", "c"} (size 3)
    # Test empty sets
    assert jaccard_similarity(set(), set()) == 0.0

def test_extract_features_from_report():
    mock_report = {
        "blast_radius": ["auth-service", "db-service"],
        "timeline": [
            {
                "source_type": "prometheus",
                "event_type": "metric_datapoint",
                "description": "Metric container_cpu_usage_seconds_total is high",
                "metadata": {"metric": "container_cpu_usage_seconds_total"}
            },
            {
                "source_type": "kubernetes",
                "event_type": "k8s_event",
                "description": "FailedScheduling warning on pod auth-service",
                "metadata": {"reason": "FailedScheduling"}
            },
            {
                "source_type": "loki",
                "event_type": "log_entry",
                "description": "ConnectionException failed to connect to database db-service: timeout error",
                "metadata": {}
            }
        ],
        "remediation": {"action": "restart pods"}
    }

    keys, alerts, error_tokens = extract_features_from_report(mock_report)
    
    assert "auth-service" in keys
    assert "db-service" in keys
    
    assert "container_cpu_usage_seconds_total" in alerts
    assert "FailedScheduling" in alerts
    assert "warning" in alerts or "fail" in alerts or "failed" in alerts
    
    assert "connectionexception" in error_tokens
    assert "timeout" in error_tokens

def test_memory_engine_index_and_search(db_session):
    engine = IncidentMemoryEngine(db_session)
    
    # Define past incident reports
    report_1 = {
        "blast_radius": ["redis", "auth-service"],
        "timeline": [
            {
                "source_type": "prometheus",
                "event_type": "metric_datapoint",
                "description": "redis_memory_used_bytes high",
                "metadata": {"metric": "redis_memory_used_bytes"}
            },
            {
                "source_type": "loki",
                "event_type": "log_entry",
                "description": "OutOfMemory error on redis cache",
                "metadata": {}
            }
        ],
        "remediation": {"action": "resize Redis cache"}
    }
    
    report_2 = {
        "blast_radius": ["db-service"],
        "timeline": [
            {
                "source_type": "prometheus",
                "event_type": "metric_datapoint",
                "description": "pg_stat_database_xact_commit low",
                "metadata": {"metric": "pg_stat_database_xact_commit"}
            },
            {
                "source_type": "loki",
                "event_type": "log_entry",
                "description": "database timeout connection pool exhausted",
                "metadata": {}
            }
        ],
        "remediation": {"action": "kill slow DB transactions"}
    }

    # Index incidents
    assert engine.index_incident("inv-1", report_1) is True
    assert engine.index_incident("inv-2", report_2) is True
    
    # Assert DB records
    hist_records = db_session.query(HistoricalIncident).all()
    assert len(hist_records) == 2
    assert any(rec.investigation_id == "inv-1" for rec in hist_records)
    assert any(rec.investigation_id == "inv-2" for rec in hist_records)
    
    # Query similar to inv-1
    matches = engine.find_similar_incidents(
        active_keys=["redis", "auth-service"],
        active_alerts=["redis_memory_used_bytes"],
        active_tokens=["outofmemory", "cache"],
        threshold=0.2
    )
    
    assert len(matches) > 0
    best_match = matches[0]
    assert best_match["investigation_id"] == "inv-1"
    assert best_match["similarity"] > 0.5
    assert best_match["remediation_action"] == {"action": "resize Redis cache"}

    # Query with non-matching features (should not return match or lower similarity)
    matches_db = engine.find_similar_incidents(
        active_keys=["db-service"],
        active_alerts=["pg_stat_database_xact_commit"],
        active_tokens=["database", "timeout"],
        threshold=0.2
    )
    assert len(matches_db) > 0
    assert matches_db[0]["investigation_id"] == "inv-2"


@pytest.mark.asyncio
async def test_pipeline_memory_integration(db_session):
    from backend.app.domain.incidents.pipeline import InvestigationPipeline
    from backend.app.domain.incidents.models import Investigation, InvestigationStatus
    import os
    from backend.app.events.store import EventStore

    # Run first investigation pipeline
    inv1_id = "inv-pipeline-1"
    inv1 = Investigation(id=inv1_id, status=InvestigationStatus.QUEUED)
    db_session.add(inv1)
    db_session.commit()

    pipeline1 = InvestigationPipeline(db_session)
    await pipeline1.execute(inv1_id)

    # Verify first pipeline ran successfully and is registered in memory database
    hist_records = db_session.query(HistoricalIncident).all()
    assert len(hist_records) == 1
    assert hist_records[0].investigation_id == inv1_id

    # Run second investigation pipeline (collecting similar mock telemetry data)
    inv2_id = "inv-pipeline-2"
    inv2 = Investigation(id=inv2_id, status=InvestigationStatus.QUEUED)
    db_session.add(inv2)
    db_session.commit()

    pipeline2 = InvestigationPipeline(db_session)
    await pipeline2.execute(inv2_id)

    # Verify second pipeline also got indexed
    assert len(db_session.query(HistoricalIncident).all()) == 2

    # Load report of the second investigation and verify similar_incidents contains inv-pipeline-1
    store = EventStore()
    report_path = os.path.join(store.base_dir, inv2_id, "report.json")
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert inv1_id in report["similar_incidents"]
    assert "remediation" in report

