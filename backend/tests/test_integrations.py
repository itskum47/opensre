import os
import shutil
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.domain.incidents.models import Investigation, InvestigationStatus
from backend.app.domain.incidents.pipeline import InvestigationPipeline
from sdk.plugin import DataSourcePlugin
from backend.app.providers.prometheus import PrometheusDataSource
from backend.app.providers.loki import LokiDataSource
from backend.app.providers.kubernetes import KubernetesDataSource
from backend.app.providers.github import GitHubDataSource
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

def test_datasource_plugin_inheritance():
    # Verify inheritance
    assert issubclass(PrometheusDataSource, DataSourcePlugin)
    assert issubclass(LokiDataSource, DataSourcePlugin)
    assert issubclass(KubernetesDataSource, DataSourcePlugin)
    assert issubclass(GitHubDataSource, DataSourcePlugin)

@pytest.mark.asyncio
async def test_prometheus_loki_collection(db_session):
    # Setup test investigation
    investigation_id = "test-integration-inv-id"
    inv = Investigation(id=investigation_id, status=InvestigationStatus.QUEUED)
    db_session.add(inv)
    db_session.commit()

    # Clean up any existing event store files for this investigation first
    event_store = EventStore()
    inv_dir = os.path.join(event_store.base_dir, investigation_id)
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)

    # Mock live HTTP client calls to assert they work as expected
    mock_prometheus_response = MagicMock()
    mock_prometheus_response.status_code = 200
    mock_prometheus_response.json.return_value = {
        "status": "success",
        "data": {"resultType": "matrix", "result": [{"metric": {"pod": "test-pod"}, "values": [[1700000000, "0.1"]]}]}
    }

    mock_loki_response = MagicMock()
    mock_loki_response.status_code = 200
    mock_loki_response.json.return_value = {
        "status": "success",
        "data": {"resultType": "streams", "result": [{"stream": {"app": "test"}, "values": [["1700000000000000000", "test log"]]}]}
    }

    mock_github_response = MagicMock()
    mock_github_response.status_code = 200
    mock_github_response.json.return_value = [
        {"sha": "testsha", "commit": {"message": "test msg", "author": {"name": "test", "date": "2026-06-07T10:00:00Z"}}, "html_url": "http://github"}
    ]

    # Mock K8s API client
    mock_pod = MagicMock()
    mock_pod.metadata.name = "k8s-pod"
    mock_pod.metadata.namespace = "default"
    mock_pod.status.phase = "Running"
    mock_pod.status.pod_ip = "10.244.0.10"

    mock_pods_list = MagicMock()
    mock_pods_list.items = [mock_pod]

    mock_event = MagicMock()
    mock_event.type = "Normal"
    mock_event.reason = "Created"
    mock_event.message = "Created pod"
    mock_event.involved_object.kind = "Pod"
    mock_event.involved_object.name = "k8s-pod"
    mock_event.last_timestamp = MagicMock()
    mock_event.last_timestamp.isoformat.return_value = "2026-06-07T10:00:00Z"

    mock_events_list = MagicMock()
    mock_events_list.items = [mock_event]

    # Setup mocks
    with patch("httpx.AsyncClient.get") as mock_get, \
         patch("backend.app.providers.kubernetes.K8S_AVAILABLE", True), \
         patch("kubernetes.config.load_incluster_config") as mock_incluster, \
         patch("kubernetes.config.load_kube_config") as mock_kubeconfig, \
         patch("kubernetes.client.CoreV1Api") as mock_core_api, \
         patch("kubernetes.client.AppsV1Api") as mock_apps_api:

        # Mock K8S setup
        mock_core_instance = MagicMock()
        mock_core_instance.list_namespaced_pod.return_value = mock_pods_list
        mock_core_instance.list_namespaced_event.return_value = mock_events_list
        mock_core_instance.list_namespaced_service.return_value = MagicMock(items=[])
        mock_core_api.return_value = mock_core_instance

        mock_apps_instance = MagicMock()
        mock_apps_instance.list_namespaced_deployment.return_value = MagicMock(items=[])
        mock_apps_api.return_value = mock_apps_instance

        # Mock http responses
        async def side_effect(url, *args, **kwargs):
            if "query_range" in url and "loki" in url:
                return mock_loki_response
            elif "query_range" in url:
                return mock_prometheus_response
            elif "github" in url or "commits" in url:
                return mock_github_response
            raise ValueError(f"Unexpected url: {url}")

        mock_get.side_effect = side_effect

        # Run pipeline with live/mock disabled (force httpx and kubernetes client)
        # We override settings to mock=False to force client calls
        with patch("backend.app.providers.prometheus.settings.API_ENV", "production"), \
             patch("backend.app.providers.loki.settings.API_ENV", "production"), \
             patch("backend.app.providers.kubernetes.settings.API_ENV", "production"), \
             patch("backend.app.providers.github.settings.API_ENV", "production"):
            
            pipeline = InvestigationPipeline(db_session)
            await pipeline.collect(investigation_id)

    # 4. Verify EventStore contents
    events = event_store.get_events(investigation_id)
    assert len(events) == 4

    source_types = [e["source_type"] for e in events]
    assert "prometheus" in source_types
    assert "loki" in source_types
    assert "kubernetes" in source_types
    assert "github" in source_types

    # Verify payloads
    prometheus_event = next(e for e in events if e["source_type"] == "prometheus")
    assert prometheus_event["payload"]["status"] == "success"

    # Clean up after test
    if os.path.exists(inv_dir):
        shutil.rmtree(inv_dir)
