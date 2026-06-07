# Phase 2: Integrations (Sprint 2) - Research

**Researched:** 2026-06-07
**Confidence:** HIGH

## Overview
This document details the APIs and connection methods required for Phase 2 integrations. It defines the endpoint specifications for Prometheus, Loki, Kubernetes, and GitHub, and specifies the base interfaces for data sources.

---

## Technical Specifications

### 1. Prometheus REST API
- **Endpoint**: `/api/v1/query_range`
- **Method**: `GET`
- **Query Params**:
  - `query`: The PromQL expression (e.g. `sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)`).
  - `start`: Start timestamp (RFC3339 or Unix timestamp).
  - `end`: End timestamp.
  - `step`: Time step interval (e.g. `15s`).
- **Response Format**: JSON containing `status: "success"` and metric coordinates (`data: { resultType: "matrix", result: [...] }`).

### 2. Loki REST API
- **Endpoint**: `/loki/api/v1/query_range`
- **Method**: `GET`
- **Query Params**:
  - `query`: LogQL expression (e.g. `{app="redis"}`).
  - `start`: Start timestamp in nanoseconds since Epoch.
  - `end`: End timestamp in nanoseconds since Epoch.
  - `limit`: Capped at 1000 lines.
- **Response Format**: JSON containing `data: { resultType: "streams", result: [ { stream: {...}, values: [[timestamp, log_line], ...] } ] }`.

### 3. Kubernetes client-python API
- **Client library**: `kubernetes`
- **Core APIs**:
  - `kubernetes.config.load_incluster_config()` and `kubernetes.config.load_kube_config()`.
  - `client.CoreV1Api()`:
    - `list_namespaced_pod(namespace)`
    - `list_namespaced_event(namespace)`
    - `list_namespaced_service(namespace)`
  - `client.AppsV1Api()`:
    - `list_namespaced_deployment(namespace)`
- **Response Format**: Serialized Python dictionaries mapping statuses and resource specifications.

### 4. GitHub REST API
- **Endpoint**: `/repos/{owner}/{repo}/commits`
- **Headers**: `Authorization: Bearer <PAT>` and `Accept: application/vnd.github.v3+json`.
- **Query Params**:
  - `since`: ISO 8601 start time.
  - `until`: ISO 8601 end time.
- **Response Format**: List of commit objects containing `sha`, `commit.message`, `commit.author`, and `html_url`.

### 5. Plugin SDK: DataSourcePlugin
In `sdk/plugin.py`, we define the base class:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class DataSourcePlugin(ABC):
    @abstractmethod
    def get_source_type(self) -> str:
        pass

    @abstractmethod
    async def collect_evidence(self, investigation_id: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
```

---

## Validation Strategy

To validate integrations programmatically, we require:
- **Mock REST Clients**: We will implement mock server handlers or `pytest` HTTP mocking (e.g. `respx` or manual helper mocks) simulating Prometheus and Loki endpoints.
- **Mock K8s API**: Mock the K8s CoreV1Api and AppsV1Api to yield predictable cluster resources.
- **Mock GitHub API**: Return mock commit lists for specific time windows.

---
*Research completed: 2026-06-07*
