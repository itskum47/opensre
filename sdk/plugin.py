from abc import ABC, abstractmethod
from typing import Dict, Any, List

class DataSourcePlugin(ABC):
    @abstractmethod
    def get_source_type(self) -> str:
        """Returns the identifier string of the data source type (e.g. 'prometheus', 'loki', 'kubernetes', 'github')."""
        pass

    @abstractmethod
    async def collect_evidence(self, investigation_id: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collects evidence files/events from the data source and returns a list of normalized event dictionaries."""
        pass
