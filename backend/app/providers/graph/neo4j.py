import logging
import re
from typing import Dict, Any
from neo4j import GraphDatabase
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class Neo4jConnector:
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j database.")
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j database: {e}. Falling back to offline mode.")
            self.driver = None

    def close(self):
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                logger.warning(f"Error closing Neo4j driver: {e}")
            finally:
                self.driver = None

    def sync_node(self, investigation_id: str, name: str, node_type: str, metadata: Dict[str, Any] = None) -> bool:
        if not self.driver:
            logger.debug(f"Offline fallback: Skipping sync_node '{name}' (type={node_type})")
            return False
        
        query = (
            "MERGE (n:IncidentNode {name: $name, investigation_id: $investigation_id}) "
            "SET n.type = $node_type, n.metadata = $metadata "
            "RETURN n"
        )
        try:
            with self.driver.session() as session:
                session.execute_write(
                    lambda tx: tx.run(
                        query,
                        name=name,
                        investigation_id=investigation_id,
                        node_type=node_type,
                        metadata=metadata or {}
                    )
                )
            return True
        except Exception as e:
            logger.warning(f"Failed to sync node '{name}' to Neo4j: {e}. Falling back gracefully.")
            return False

    def sync_edge(self, investigation_id: str, source: str, target: str, relationship: str, metadata: Dict[str, Any] = None) -> bool:
        if not self.driver:
            logger.debug(f"Offline fallback: Skipping sync_edge '{source}' -> '{target}'")
            return False

        # Sanitize relationship type to prevent Cypher injection
        rel_type = relationship.upper()
        if not re.match(r"^[A-Z0-9_]+$", rel_type):
            rel_type = "RELATED_TO"

        query = (
            f"MATCH (a:IncidentNode {{name: $source, investigation_id: $investigation_id}}) "
            f"MATCH (b:IncidentNode {{name: $target, investigation_id: $investigation_id}}) "
            f"MERGE (a)-[r:{rel_type}]->(b) "
            f"SET r.investigation_id = $investigation_id, r.metadata = $metadata "
            f"RETURN r"
        )
        try:
            with self.driver.session() as session:
                session.execute_write(
                    lambda tx: tx.run(
                        query,
                        source=source,
                        target=target,
                        investigation_id=investigation_id,
                        metadata=metadata or {}
                    )
                )
            return True
        except Exception as e:
            logger.warning(f"Failed to sync edge '{source}' -> '{target}' to Neo4j: {e}. Falling back gracefully.")
            return False
