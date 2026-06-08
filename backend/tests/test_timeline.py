import os
import json
import shutil
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.pipeline import InvestigationPipeline
from backend.app.domain.incidents.timeline import TimelineBuilder, CorrelationEngine
from backend.app.events.store import EventStore

@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

def test_timeline_compilation_and_correlation():
    store = EventStore()
    investigation_id = "test-timeline-inv-id"
    inv_dir = os.path.join(store.base_dir, investigation_id)
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

    # 1. Write mock events directly to the store
    # A Prometheus event
    store.write_event(
        investigation_id=investigation_id,
        source_type="prometheus",
        source_id="cpu_usage",
        payload={
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [{
                    "metric": {"pod": "auth-service-xyz", "__name__": "cpu"},
                    "values": [["1780000000", "0.85"], ["1780000300", "0.90"]]
                }]
            }
        }
    )

    # A Loki log event (happens at 1780000100 seconds = 1780000100000000000 nanoseconds)
    store.write_event(
        investigation_id=investigation_id,
        source_type="loki",
        source_id="redis_logs",
        payload={
            "status": "success",
            "data": {
                "resultType": "streams",
                "result": [{
                    "stream": {"pod": "auth-service-xyz"},
                    "values": [["1780000100000000000", "Error connection refused"]]
                }]
            }
        }
    )

    # A GitHub commit event (happens earlier at 1780000000)
    store.write_event(
        investigation_id=investigation_id,
        source_type="github",
        source_id="repository_commits",
        payload=[{
            "sha": "abcdef12345",
            "commit": {
                "message": "fix: auth database connection",
                "author": {"name": "Kumar", "email": "k@k.com", "date": "2026-06-07T09:40:00Z"}
            },
            "html_url": "http://github"
        }]
    )

    # Build timeline
    builder = TimelineBuilder(store)
    raw_timeline = builder.build_raw_timeline(investigation_id)

    # Check chronological sorting
    assert len(raw_timeline) > 0
    timestamps = [e["timestamp"] for e in raw_timeline]
    # Ensure they are sorted
    assert timestamps == sorted(timestamps)

    # Correlate
    engine = CorrelationEngine(window_seconds=300)
    groups = engine.correlate_events(raw_timeline)

    # We should have at least one correlated group containing our auth-service events
    assert len(groups) > 0
    auth_groups = [g for g in groups if any("auth-service" in k for k in g["keys"])]
    assert len(auth_groups) > 0

    # Clean up
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

@pytest.mark.asyncio
async def test_pipeline_timeline_execution(db_session):
    investigation_id = "test-pipeline-timeline-inv-id"
    inv = Investigation(id=investigation_id, status=InvestigationStatus.QUEUED)
    db_session.add(inv)
    db_session.commit()

    # Pre-populate store with mock events
    store = EventStore()
    inv_dir = os.path.join(store.base_dir, investigation_id)
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

    store.write_event(
        investigation_id=investigation_id,
        source_type="kubernetes",
        source_id="cluster_resources",
        payload={
            "pods": [{"name": "auth-service-xyz", "status": "Running"}],
            "events": [{"type": "Warning", "reason": "Failed", "message": "Failed probe", "object": "Pod/auth-service-xyz", "timestamp": "2026-06-07T10:00:00Z"}]
        }
    )

    pipeline = InvestigationPipeline(db_session)
    await pipeline.execute(investigation_id)

    # Check that timeline.json and correlated_groups.json were written
    timeline_file = os.path.join(inv_dir, "timeline.json")
    groups_file = os.path.join(inv_dir, "correlated_groups.json")

    assert os.path.exists(timeline_file)
    assert os.path.exists(groups_file)

    with open(timeline_file, "r") as f:
        timeline_data = json.load(f)
    assert len(timeline_data) > 0

    # Clean up
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)
