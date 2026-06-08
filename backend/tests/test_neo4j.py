from unittest.mock import MagicMock, patch
from backend.app.providers.graph.neo4j import Neo4jConnector

def test_neo4j_offline_fallback():
    connector = Neo4jConnector()
    with patch("backend.app.providers.graph.neo4j.GraphDatabase.driver") as mock_driver:
        # Simulate connection failure
        mock_driver.side_effect = Exception("Connection refused")
        connector.connect()
        assert connector.driver is None

    # Sync node/edge should fail gracefully and return False
    assert connector.sync_node("test-id", "service-a", "service") is False
    assert connector.sync_edge("test-id", "service-a", "service-b", "DEPENDS_ON") is False

def test_neo4j_online_sync():
    connector = Neo4jConnector()
    
    mock_driver_instance = MagicMock()
    mock_session = MagicMock()
    mock_driver_instance.session.return_value.__enter__.return_value = mock_session
    
    with patch("backend.app.providers.graph.neo4j.GraphDatabase.driver") as mock_driver_factory:
        mock_driver_factory.return_value = mock_driver_instance
        connector.connect()
        assert connector.driver == mock_driver_instance

    # Test node sync
    mock_session.execute_write.side_effect = lambda fn: fn(MagicMock())
    
    res_node = connector.sync_node("test-id", "service-a", "service", {"key": "val"})
    assert res_node is True
    assert mock_session.execute_write.called

    # Test edge sync
    res_edge = connector.sync_edge("test-id", "service-a", "service-b", "DEPENDS_ON", {"latency": 10})
    assert res_edge is True

    connector.close()
    assert connector.driver is None
