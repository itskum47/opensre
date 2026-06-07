import logging
from typing import Dict, Any, List
from sdk.plugin import DataSourcePlugin
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

# Lazy import kubernetes to allow graceful fallback if the module is missing
try:
    import kubernetes
    from kubernetes import client
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

class KubernetesDataSource(DataSourcePlugin):
    def __init__(self, mock: bool = False):
        self.mock = mock or (settings.API_ENV == "development")
        self.k8s_loaded = False
        
        if K8S_AVAILABLE and not self.mock:
            try:
                kubernetes.config.load_incluster_config()
                self.k8s_loaded = True
            except Exception:
                try:
                    kubernetes.config.load_kube_config()
                    self.k8s_loaded = True
                except Exception as e:
                    logger.warning(f"Could not load Kubernetes configuration: {e}")
                    self.k8s_loaded = False

    def get_source_type(self) -> str:
        return "kubernetes"

    async def collect_evidence(self, investigation_id: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        namespace = query_params.get("namespace", "default")
        is_mock = query_params.get("mock", self.mock) or not self.k8s_loaded or not K8S_AVAILABLE
        
        if is_mock:
            # Return mock K8s cluster status evidence
            mock_payload = {
                "pods": [
                    {"name": "auth-service-xyz", "namespace": namespace, "status": "Running", "ip": "10.244.0.12"},
                    {"name": "db-service-abc", "namespace": namespace, "status": "Running", "ip": "10.244.0.15"}
                ],
                "deployments": [
                    {"name": "auth-service", "namespace": namespace, "replicas": 1, "available_replicas": 1},
                    {"name": "db-service", "namespace": namespace, "replicas": 1, "available_replicas": 1}
                ],
                "services": [
                    {"name": "auth-service", "namespace": namespace, "cluster_ip": "10.96.0.12"},
                    {"name": "db-service", "namespace": namespace, "cluster_ip": "10.96.0.15"}
                ],
                "events": [
                    {
                        "type": "Warning",
                        "reason": "Unhealthy",
                        "message": "Readiness probe failed: HTTP probe failed with statuscode: 500",
                        "object": "Pod/auth-service-xyz",
                        "timestamp": "2026-06-07T10:00:00Z"
                    }
                ]
            }
            return [{
                "source_id": "cluster_resources",
                "payload": mock_payload
            }]

        try:
            core_api = client.CoreV1Api()
            apps_api = client.AppsV1Api()
            
            # 1. List Pods
            pods_list = core_api.list_namespaced_pod(namespace=namespace)
            pods = []
            for pod in pods_list.items:
                pods.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip
                })
                
            # 2. List Deployments
            deployments_list = apps_api.list_namespaced_deployment(namespace=namespace)
            deployments = []
            for dep in deployments_list.items:
                deployments.append({
                    "name": dep.metadata.name,
                    "namespace": dep.metadata.namespace,
                    "replicas": dep.spec.replicas,
                    "available_replicas": dep.status.available_replicas
                })
                
            # 3. List Services
            services_list = core_api.list_namespaced_service(namespace=namespace)
            services = []
            for svc in services_list.items:
                services.append({
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "cluster_ip": svc.spec.cluster_ip
                })
                
            # 4. List Events
            events_list = core_api.list_namespaced_event(namespace=namespace)
            events = []
            for ev in events_list.items:
                events.append({
                    "type": ev.type,
                    "reason": ev.reason,
                    "message": ev.message,
                    "object": f"{ev.involved_object.kind}/{ev.involved_object.name}",
                    "timestamp": ev.last_timestamp.isoformat() if ev.last_timestamp else None
                })
                
            payload = {
                "pods": pods,
                "deployments": deployments,
                "services": services,
                "events": events
            }
            return [{
                "source_id": "cluster_resources",
                "payload": payload
            }]
            
        except Exception as e:
            logger.error(f"Failed to query Kubernetes API: {e}")
            raise e
