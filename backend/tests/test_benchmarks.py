import os
import json
import shutil
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.pipeline import InvestigationPipeline
from backend.app.events.store import EventStore

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_benchmark_redis_saturation(db_session):
    investigation_id = "bench-redis-saturation"
    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    ts_unix = int(started_at.timestamp())
    ts_ns = ts_unix * 1000000000
    ts_iso = started_at.isoformat().replace("+00:00", "Z")
    
    # Create investigation
    inv = Investigation(
        id=investigation_id,
        status=InvestigationStatus.QUEUED,
        started_at=started_at
    )
    db_session.add(inv)
    db_session.commit()

    store = EventStore()
    inv_dir = os.path.join(store.base_dir, investigation_id)
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

    # 1. Prometheus high CPU metric event (marked critical to register as anomaly)
    prometheus_payload = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"pod": "redis-prod-0", "__name__": "redis_cpu_critical_level"},
                    "values": [[str(ts_unix), "0.95"]]
                }
            ]
        }
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="prometheus",
        source_id="cpu_usage",
        payload=prometheus_payload
    )

    # 2. Loki log memory warning event
    loki_payload = {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"pod": "redis-prod-0", "app": "redis"},
                    "values": [
                        [str(ts_ns), "warning: redis memory saturation detected, running out of memory"]
                    ]
                }
            ]
        }
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="loki",
        source_id="redis_logs",
        payload=loki_payload
    )

    # 3. K8s readiness failure event
    kubernetes_payload = {
        "events": [
            {
                "timestamp": ts_iso,
                "type": "Warning",
                "reason": "Unhealthy",
                "object": "Pod/redis-prod-0",
                "message": "Readiness probe failed: connection refused error"
            }
        ],
        "pods": [
            {
                "name": "redis-prod-0",
                "status": "Unhealthy",
                "ip": "10.244.1.20"
            }
        ]
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="kubernetes",
        source_id="cluster_resources",
        payload=kubernetes_payload
    )

    # 4. Optional lower-priority noise event
    noise_prometheus_payload = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"pod": "auth-service-xyz", "__name__": "cpu"},
                    "values": [[str(ts_unix), "0.10"]]
                }
            ]
        }
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="prometheus",
        source_id="noise_cpu",
        payload=noise_prometheus_payload
    )

    # Instantiate pipeline
    pipeline = InvestigationPipeline(db_session)
    
    # Mock collect to prevent overwriting the stored events
    pipeline.collect = AsyncMock()

    # Execute full pipeline
    await pipeline.execute(investigation_id)

    # Assert completed
    db_session.refresh(inv)
    assert inv.status == InvestigationStatus.COMPLETED

    # Verify report is created and ranks Redis first
    report_file = os.path.join(inv_dir, "report.json")
    assert os.path.exists(report_file)

    with open(report_file, "r") as f:
        report_data = json.load(f)

    # Assert Redis is in the root cause and ranks #1
    assert "redis" in report_data["root_cause"].lower()
    assert report_data["confidence"] >= 75.0
    assert any("redis" in key for key in report_data["blast_radius"])

    # Clean up
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

@pytest.mark.asyncio
async def test_benchmark_database_outage(db_session):
    investigation_id = "bench-db-outage"
    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    ts_unix = int(started_at.timestamp())
    ts_ns = ts_unix * 1000000000
    ts_iso = started_at.isoformat().replace("+00:00", "Z")
    
    # Create investigation
    inv = Investigation(
        id=investigation_id,
        status=InvestigationStatus.QUEUED,
        started_at=started_at
    )
    db_session.add(inv)
    db_session.commit()

    store = EventStore()
    inv_dir = os.path.join(store.base_dir, investigation_id)
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

    # 1. GitHub commit event modifying DB/postgres schema (contains "failure" for anomaly check)
    github_payload = [
        {
            "sha": "dbcommitsha123",
            "commit": {
                "message": "migration: alter postgres schema to fix database failure",
                "author": {
                    "name": "dev",
                    "email": "dev@company.com",
                    "date": ts_iso
                }
            },
            "html_url": "https://github.com/org/repo/commit/dbcommitsha123"
        }
    ]
    store.write_event(
        investigation_id=investigation_id,
        source_type="github",
        source_id="repository_commits",
        payload=github_payload
    )

    # 2. Loki log pool exhaustion event
    loki_payload = {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"pod": "postgres-db-0", "app": "postgres"},
                    "values": [
                        [str(ts_ns), "error: postgres connection pool exhausted, database unavailable"]
                    ]
                }
            ]
        }
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="loki",
        source_id="postgres_logs",
        payload=loki_payload
    )

    # 3. K8s CrashLoopBackOff event
    kubernetes_payload = {
        "events": [
            {
                "timestamp": ts_iso,
                "type": "Warning",
                "reason": "CrashLoopBackOff",
                "object": "Pod/postgres-db-0",
                "message": "Back-off restarting failed container postgres"
            }
        ],
        "pods": [
            {
                "name": "postgres-db-0",
                "status": "Unhealthy",
                "ip": "10.244.1.30"
            }
        ]
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="kubernetes",
        source_id="cluster_resources",
        payload=kubernetes_payload
    )

    # 4. Noise event
    noise_prometheus_payload = {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"pod": "auth-service-xyz", "__name__": "cpu"},
                    "values": [[str(ts_unix), "0.10"]]
                }
            ]
        }
    }
    store.write_event(
        investigation_id=investigation_id,
        source_type="prometheus",
        source_id="noise_cpu",
        payload=noise_prometheus_payload
    )

    # Instantiate pipeline
    pipeline = InvestigationPipeline(db_session)
    
    # Mock collect
    pipeline.collect = AsyncMock()

    # Execute full pipeline
    await pipeline.execute(investigation_id)

    # Assert completed
    db_session.refresh(inv)
    assert inv.status == InvestigationStatus.COMPLETED

    # Verify report is created and ranks database first
    report_file = os.path.join(inv_dir, "report.json")
    assert os.path.exists(report_file)

    with open(report_file, "r") as f:
        report_data = json.load(f)

    # Assert postgres/db is in the root cause and ranks #1
    assert any(term in report_data["root_cause"].lower() for term in ["postgres", "db"])
    assert report_data["confidence"] >= 75.0
    assert any(any(term in key for term in ["postgres", "db"]) for key in report_data["blast_radius"])

    # Clean up
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)
