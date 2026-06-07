import httpx
import logging
from typing import Dict, Any, List
from sdk.plugin import DataSourcePlugin
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class PrometheusDataSource(DataSourcePlugin):
    def __init__(self, prometheus_url: str = None, mock: bool = False):
        self.prometheus_url = prometheus_url or settings.PROMETHEUS_URL
        self.mock = mock or (settings.API_ENV == "development")

    def get_source_type(self) -> str:
        return "prometheus"

    async def collect_evidence(self, investigation_id: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = query_params.get("query", "sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)")
        start = query_params.get("start")
        end = query_params.get("end")
        step = query_params.get("step", "15s")
        
        # Check if mock mode is requested in call or instance level
        is_mock = query_params.get("mock", self.mock)
        
        if is_mock:
            try:
                start_val = int(start) if start is not None else 1700000000
            except ValueError:
                start_val = 1700000000

            # Return realistic mock Prometheus CPU usage data
            mock_payload = {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"pod": "auth-service-xyz", "__name__": "container_cpu_usage_seconds_total"},
                            "values": [
                                [start_val, "0.15"],
                                [start_val + 15, "0.18"],
                                [start_val + 30, "0.22"]
                            ]
                        },
                        {
                            "metric": {"pod": "db-service-abc", "__name__": "container_cpu_usage_seconds_total"},
                            "values": [
                                [start_val, "0.45"],
                                [start_val + 15, "0.48"],
                                [start_val + 30, "0.52"]
                            ]
                        }
                    ]
                }
            }
            return [{
                "source_id": "cpu_usage",
                "payload": mock_payload
            }]


        url = f"{self.prometheus_url.rstrip('/')}/api/v1/query_range"
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return [{
                    "source_id": "cpu_usage",
                    "payload": response.json()
                }]
        except Exception as e:
            logger.error(f"Failed to query Prometheus: {e}")
            raise e
