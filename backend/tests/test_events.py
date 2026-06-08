import os
import pytest
import shutil
from backend.app.events.store import EventStore

@pytest.fixture
def temp_event_store(tmp_path):
    store_dir = tmp_path / "events"
    yield EventStore(base_dir=str(store_dir))
    if store_dir.exists():
        shutil.rmtree(store_dir)

def test_event_store_write_and_read(temp_event_store):
    investigation_id = "test-inv-123"
    payload = {"status": "cpu_spike", "value": 98.5}
    
    filepath = temp_event_store.write_event(investigation_id, "prometheus", "cpu_metric", payload)
    assert os.path.exists(filepath)
    
    events = temp_event_store.get_events(investigation_id)
    assert len(events) == 1
    assert events[0]["source_type"] == "prometheus"
    assert events[0]["source_id"] == "cpu_metric"
    assert events[0]["payload"] == payload

def test_event_store_immutable(temp_event_store):
    investigation_id = "test-inv-123"
    payload = {"data": "test"}
    filepath = temp_event_store.write_event(investigation_id, "test_source", "test_id", payload)
    
    # Assert writing same file twice or editing raises an exception in logic
    # Try to write again and verify we generate unique timestamps/files
    filepath_2 = temp_event_store.write_event(investigation_id, "test_source", "test_id", payload)
    assert filepath != filepath_2
