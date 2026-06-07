import networkx as nx
from typing import Dict, Any, List

class GraphProvider:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, name: str, node_type: str = "service", metadata: Dict[str, Any] = None):
        self.graph.add_node(name, type=node_type, metadata=metadata or {})

    def add_edge(self, source: str, target: str, relationship: str = "depends_on", metadata: Dict[str, Any] = None):
        self.graph.add_edge(source, target, relationship=relationship, metadata=metadata or {})

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

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph structure for storage."""
        return {
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
        provider = cls()
        for node in data.get("nodes", []):
            provider.add_node(node["name"], node_type=node.get("type", "service"), metadata=node.get("metadata"))
        for edge in data.get("edges", []):
            provider.add_edge(edge["source"], edge["target"], relationship=edge.get("relationship", "depends_on"), metadata=edge.get("metadata"))
        return provider
