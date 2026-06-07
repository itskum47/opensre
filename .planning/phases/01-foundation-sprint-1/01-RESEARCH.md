# Phase 1: Foundation (Sprint 1) - Research

**Researched:** 2026-06-07
**Confidence:** HIGH

## Overview
This document outlines the technical research and domain patterns required to implement Phase 1: Foundation. It details the setup of the FastAPI backend, Celery + Redis worker queue, Event Store directories, SQLAlchemy models, custom LLM Router, snapshot format, Docker compose environment, and GitHub Actions/GitLab CI configurations.

---

## Technical Architecture & Libraries

### 1. Backend Core & FastAPI
FastAPI will host the API endpoints. The project directory structure follows the Monorepo architecture specified in [ARCHITECTURE.md](file:///Users/kumarmangalam/Desktop/Projects/.planning/research/ARCHITECTURE.md).
- FastAPI `FastAPI()` is configured with lifespan events to handle initialization and shutdown of database pools and Celery hooks.
- Routing is defined under `backend/app/api/routers/` (e.g. `investigations.py` for API routes).
- Business logic is strictly isolated in `backend/app/domain/` to avoid mixing controller and logic layers.

### 2. Celery + Redis Task Queue
Celery will process the asynchronous `InvestigationPipeline` jobs.
- **Broker**: `redis://localhost:6379/0`
- **Result Backend**: `redis://localhost:6379/1`
- **Configuration**:
  - `task_serializer = "json"`
  - `result_serializer = "json"`
  - `accept_content = ["json"]`
  - `timezone = "UTC"`
  - `enable_utc = True`
  - `task_track_started = True` (critical for transition states: QUEUED -> COLLECTING, etc.)
- **Worker Dispatch**: API endpoint calls `investigate_task.delay(investigation_id)` and returns a `job_id` (the Celery Task ID) immediately.

### 3. Immutable Event Store & Snapshots
- **Event Store Directory**: `backend/app/events/`
- Raw evidence files are persisted as JSON: `backend/app/events/{investigation_id}/{source_type}_{source_id}_{timestamp}.json`.
- Snapshots are written to a separate folder: `backend/app/snapshots/{investigation_id}_snapshot.json`.
- Snapshots contain:
  - `schema_version`: "1.0"
  - `raw_events`: List of references or embedded copies of Event Store entries.
  - `timeline`: Deterministic chronological sequence.
  - `graph`: NetworkX serialized format (JSON nodes/edges).
  - `findings`: Evidence-backed RCA findings.
  - `report`: IncidentReportV1 document.
  - `metadata`: `{"pipeline_version": "1.0", "ranking_version": "1.0", "graph_version": "1.0", "prompt_version": "1.0", "model": "gemini-2.5-pro", "temperature": 0.0}`.

### 4. Database Schema (Audit Trail & Registries)
SQLAlchemy with SQLite maps the database state.
- **Investigation Table**:
  - `id` (UUID or String PK)
  - `status` (Enum: QUEUED, COLLECTING, NORMALIZING, CORRELATING, TIMELINE, GRAPHING, HYPOTHESIZING, RANKING, REPORTING, COMPLETED, FAILED)
  - `started_at` (DateTime)
  - `completed_at` (DateTime, Nullable)
  - `duration` (Float, Nullable)
  - `pipeline_version` (String)
  - `report_id` (String, Nullable)
- **AuditTrail Table**:
  - `id` (Integer PK)
  - `timestamp` (DateTime)
  - `action` (String: e.g. "investigation_created", "evidence_collected", etc.)
  - `investigation_id` (String FK)
  - `payload` (JSON/String: metadata details)
  - *Constraint*: Immutable (no UPDATE or DELETE methods exposed in services).

### 5. Custom LLMProvider Abstraction
Direct calls to OpenAI, Anthropic, Gemini, Ollama, and OpenRouter are banned. They must extend `LLMProvider`:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_structured(self, prompt: str, response_model: Type[BaseModel], **kwargs) -> BaseModel:
        """Enforces Pydantic structured output validation."""
        pass
```
- **Fallback Router Pattern**:
  - Iterates through a configured sequence of providers (e.g. Anthropic -> Gemini -> OpenRouter).
  - Catches API connections, timeout, and rate limit errors, retrying with exponential backoff (`retries=3`, `backoff_factor=2`) before falling back to the next provider in the chain.
  - A mock implementation (`MockLLMProvider`) must return pre-configured Pydantic outputs for offline test execution.

### 6. CI/CD Configuration
- **GitHub Actions (`.github/workflows/ci.yml`)**:
  - Runs on `push` and `pull_request` to `main` / `master`.
  - Sets up Python 3.12, Redis service container, installs poetry/dependencies, runs `ruff check .` (linter) and `pytest` (test suite).
- **GitLab CI (`.gitlab-ci.yml`)**:
  - Uses `python:3.12` image.
  - Configures `services: [redis:7]` service container.
  - Runs linting and pytest testing stages.

---

## Validation Architecture

To satisfy automated pipeline validation, we require:
- **Mock Integration Verification**: Test cases executing the full `InvestigationPipeline` using mock providers and enqueued tasks, verifying that it progresses from QUEUED to COMPLETED and generates correct snapshots.
- **Audit Immutability Test**: A unit test asserting that SQL operations raising UPDATE/DELETE on the audit trail are strictly rejected or fail-fast.
- **Worker Async Integration Test**: Testing FastAPI route responses to ensure a task enqueues successfully and returns a job status query URL.

---
*Research completed: 2026-06-07*
