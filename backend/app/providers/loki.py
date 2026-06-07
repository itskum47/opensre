import httpx
import logging
import time
from typing import Dict, Any, List
from sdk.plugin import DataSourcePlugin
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class LokiDataSource(DataSourcePlugin):
    def __init__(self, loki_url: str = None, mock: bool = False):
        self.loki_url = loki_url or settings.LOKI_URL
        self.mock = mock or (settings.API_ENV == "development")

    def get_source_type(self) -> str:
        return "loki"

    async def collect_evidence(self, investigation_id: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = query_params.get("query", '{app="redis"}')
        start = query_params.get("start")
        end = query_params.get("end")
        limit = min(query_params.get("limit", 1000), 1000)
        
        is_mock = query_params.get("mock", self.mock)
        
        if is_mock:
            try:
                start_val = int(start) if start is not None else int(time.time() * 1e9)
            except ValueError:
                start_val = int(time.time() * 1e9)

            mock_payload = {
                "status": "success",
                "data": {
                    "resultType": "streams",
                    "result": [
                        {
                            "stream": {"app": "redis", "container": "redis-master"},
                            "values": [
                                [str(start_val), "1:M 07 Jun 2026 10:00:00.000 * DB loaded from disk: 0.123 seconds"],
                                [str(start_val + 1000000), "1:M 07 Jun 2026 10:00:01.000 # Connection with replica closed"],
                                [str(start_val + 2000000), "1:M 07 Jun 2026 10:00:02.000 * Synchronization with replica succeeded"]
                            ]
                        }
                    ]
                }
            }
            return [{
                "source_id": "redis_logs",
                "payload": mock_payload
            }]


        url = f"{self.loki_url.rstrip('/')}/loki/api/v1/query_range"
        params = {
            "query": query,
            "limit": limit
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return [{
                    "source_id": "redis_logs",
                    "payload": response.json()
                }]
        except Exception as e:
            logger.error(f"Failed to query Loki: {e}")
            raise e
