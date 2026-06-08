import os
import logging
import networkx as nx
from typing import Dict, Any, List
from backend.app.providers.graph.neo4j import Neo4jConnector

logger = logging.getLogger(__name__)

class GraphProvider:
    def __init__(self, investigation_id: str = "default", enable_neo4j: bool = True):
        self.investigation_id = investigation_id
        self.graph = nx.DiGraph()
        self.neo4j = None
        # Disable Neo4j connection in test environment to avoid test slowdowns
        if enable_neo4j and os.environ.get("API_ENV") != "test":
            self.neo4j = Neo4jConnector()
            self.neo4j.connect()

    def add_node(self, name: str, node_type: str = "service", metadata: Dict[str, Any] = None):
        self.graph.add_node(name, type=node_type, metadata=metadata or {})
        if self.neo4j:
            self.neo4j.sync_node(self.investigation_id, name, node_type, metadata)

    def add_edge(self, source: str, target: str, relationship: str = "depends_on", metadata: Dict[str, Any] = None):
        self.graph.add_edge(source, target, relationship=relationship, metadata=metadata or {})
        if self.neo4j:
            self.neo4j.sync_edge(self.investigation_id, source, target, relationship, metadata)

    def get_dependencies(self, name: str) -> List[str]:
        """Returns list of nodes that this node depends on (successors in DiGraph)."""
        if name in self.graph:
            return list(self.graph.successors(name))
        return []

    def get_dependents(self, name: str) -> List[str]:
        """Returns list of nodes that depend on this node (predecessors in DiGraph)."""
        if name in self.graph:
            return list(self.graph.predecessors(name))
        return []

    def get_shared_dependencies(self, alert_names: List[str], max_hops: int = 3) -> List[str]:
        """Finds common dependencies across target alert nodes."""
        if not alert_names:
            return []

        # If Neo4j is available, run Cypher query
        if self.neo4j and self.neo4j.driver:
            max_hops_int = int(max_hops)
            query = (
                "MATCH (a:IncidentNode {investigation_id: $investigation_id}) "
                "WHERE a.name IN $alert_names "
                "MATCH (d:IncidentNode {investigation_id: $investigation_id}) "
                "WHERE NOT d.name IN $alert_names "
                f"MATCH (a)-[*1..{max_hops_int}]->(d) "
                "WITH d, count(distinct a) as alert_count "
                "WHERE alert_count = $alert_len "
                "RETURN d.name as name"
            )
            try:
                with self.neo4j.driver.session() as session:
                    result = session.run(
                        query,
                        investigation_id=self.investigation_id,
                        alert_names=alert_names,
                        alert_len=len(alert_names)
                    )
                    return [record["name"] for record in result]
            except Exception as e:
                logger.warning(f"Neo4j get_shared_dependencies query failed: {e}. Falling back to NetworkX.")

        # NetworkX Fallback
        reachable_sets = []
        for alert in alert_names:
            if alert in self.graph:
                lengths = nx.single_source_shortest_path_length(self.graph, alert, cutoff=max_hops)
                reachable_sets.append(set(lengths.keys()))
            else:
                reachable_sets.append(set())

        if not reachable_sets:
            return []

        shared = set.intersection(*reachable_sets)
        shared = shared - set(alert_names)
        return list(shared)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph structure for storage."""
        return {
            "investigation_id": self.investigation_id,
            "nodes": [
                {"name": node, "type": data.get("type", "service"), "metadata": data.get("metadata", {})}
                for node, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, "relationship": data.get("relationship", "depends_on"), "metadata": data.get("metadata", {})}
                for u, v, data in self.graph.edges(data=True)
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphProvider":
        investigation_id = data.get("investigation_id", "default")
        provider = cls(investigation_id=investigation_id)
        for node in data.get("nodes", []):
            provider.add_node(node["name"], node_type=node.get("type", "service"), metadata=node.get("metadata"))
        for edge in data.get("edges", []):
            provider.add_edge(edge["source"], edge["target"], relationship=edge.get("relationship", "depends_on"), metadata=edge.get("metadata"))
        return provider
