import pytest
from datetime import datetime, timezone
from backend.app.domain.incidents.graph import GraphProvider
from backend.app.domain.incidents.ranker import RootCauseRanker

def test_graph_provider_mapping():
    provider = GraphProvider()
    provider.add_node("auth-service", node_type="service")
    provider.add_node("db-service", node_type="database")
    provider.add_edge("auth-service", "db-service")

    assert "auth-service" in provider.graph
    assert "db-service" in provider.graph
    assert provider.get_dependencies("auth-service") == ["db-service"]
    assert provider.get_dependents("db-service") == ["auth-service"]

    # Test serialization
    data = provider.to_dict()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    # Test deserialization
    new_provider = GraphProvider.from_dict(data)
    assert "auth-service" in new_provider.graph
    assert new_provider.get_dependencies("auth-service") == ["db-service"]

def test_root_cause_ranker_scoring():
    provider = GraphProvider()
    provider.add_node("auth-service")
    provider.add_node("redis")
    provider.add_edge("auth-service", "redis")

    ranker = RootCauseRanker(provider)
    started_at = datetime(2026, 6, 7, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Setup a group with high anomalies and git commit
    group1 = {
        "group_id": "group_1",
        "keys": ["auth-service", "redis"],
        "events": [
            {
                "timestamp": "2026-06-07T10:00:10Z",
                "source_type": "loki",
                "source_id": "redis_logs",
                "event_type": "log_entry",
                "description": "Error connection refused by redis"
            },
            {
                "timestamp": "2026-06-07T09:59:50Z",
                "source_type": "github",
                "source_id": "repository_commits",
                "event_type": "git_commit",
                "description": "feat: rate limit auth service"
            }
        ]
    }

    # 2. Setup a group with no anomalies and no commits
    group2 = {
        "group_id": "group_2",
        "keys": ["other-service"],
        "events": [
            {
                "timestamp": "2026-06-07T10:05:00Z",
                "source_type": "prometheus",
                "source_id": "cpu_usage",
                "event_type": "metric_datapoint",
                "description": "Metric cpu is 0.05"
            }
        ]
    }

    candidates = ranker.rank_hypotheses(started_at, [group1, group2])

    assert len(candidates) == 2
    # Group 1 should be ranked #1
    assert candidates[0]["group_id"] == "group_1"
    assert candidates[0]["confidence_score"] > candidates[1]["confidence_score"]
    
    # Check that change_history is 1.0 for Group 1 and 0.0 for Group 2
    assert candidates[0]["metrics"]["change_history"] == 1.0
    assert candidates[1]["metrics"]["change_history"] == 0.0

def test_shared_dependencies():
    # Setup service topology
    # api-gateway -> auth-service -> db-service
    # payment-service -> db-service
    provider = GraphProvider()
    provider.add_node("api-gateway")
    provider.add_node("auth-service")
    provider.add_node("payment-service")
    provider.add_node("db-service")
    
    provider.add_edge("api-gateway", "auth-service")
    provider.add_edge("auth-service", "db-service")
    provider.add_edge("payment-service", "db-service")

    # Find shared dependencies between api-gateway and payment-service (should be db-service)
    shared = provider.get_shared_dependencies(["api-gateway", "payment-service"], max_hops=3)
    assert "db-service" in shared
    assert "auth-service" not in shared  # not dependent by payment-service
    assert "api-gateway" not in shared  # should exclude alerts themselves
