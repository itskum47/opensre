# Phase 1: Foundation (Sprint 1) - Context

**Gathered:** 2026-06-07T10:20:00+05:30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase establishes the foundational backend engine, asynchronous task queue, and testing harness for OpenSRE. It delivers a FastAPI web server, Celery task processing with Redis, an immutable file-based raw Event Store, database schemas for audits and run status tracking, a custom unified `LLMProvider` abstraction routing across five endpoints (OpenAI, Anthropic, Gemini, Ollama, OpenRouter) with fallback/backoff patterns, local Docker orchestrations, and automated CI/CD configurations for GitLab CI and GitHub Actions.

</domain>

<decisions>
## Implementation Decisions

### API / Schema & Worker Implementation
- **API Framework**: FastAPI for clean, async-first endpoints with automatic Pydantic schema validation and OpenAPI doc generation.
- **Worker Queue**: Celery with Redis broker for scalable, asynchronous investigation pipeline task running.
- **Serialization Format**: Standard, secure JSON serialization for task parameters.
- **Registry / Audit Trail Database**: SQLAlchemy ORM with SQLite backend for lightweight local development, easily upgradable to PostgreSQL for cloud deployments.

### Event Store & Snapshots
- **Event Store Format**: Immutable, write-once raw JSON files located under `backend/app/events/`.
- **Snapshot Format**: A unified JSON representation of raw events, timeline, graph, findings, report, and metadata.
- **Reproducibility Metadata**: Captured inside snapshots (schema_version, pipeline_version, graph_version, prompt_version, model, temperature).
- **Snapshot Storage**: Stored in a separate folder (`backend/app/snapshots/`) to decouple summaries from raw events.

### LLM Provider Router
- **Router Implementation**: Custom abstract base class `LLMProvider` with specific backend adapters (OpenAI, Anthropic, Gemini, Ollama, OpenRouter). LiteLLM package is avoided to reduce dependency bloat.
- **Fallback Behavior**: Dynamic provider chain routing (e.g. primary -> secondary) with exponential backoff on rate limits or service down-times.
- **Structured Output**: Strictly validate and enforce Pydantic structured output mappings on all provider completions.

### Claude's Discretion
- Code architecture file structures and modular layouts within FastAPI directory scopes are left to Claude's discretion.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None (Greenfield project).

### Established Patterns
- Monorepo directory structure: `backend/`, `cli/`, `sdk/`, `integrations/`, `infra/`, `tests/`.

### Integration Points
- None yet.

</code_context>

<specifics>
## Specific Ideas

- The `LLMProvider` must have unified mock implementations to allow running local test suites without real API keys or hitting network rate limits.
- CI/CD configurations must be written for both GitHub Actions (`.github/workflows/ci.yml`) and GitLab CI (`.gitlab-ci.yml`) to support linting, style checks (Ruff), and unit testing (pytest) automatically on every push or pull request.

</specifics>

<deferred>
## Deferred Ideas

- Neo4j graph storage and Neo4jProvider (deferred to Phase 4 / v2).
- Slack and PagerDuty interactive blocks (deferred to v2).
- Automatic auto-remediation execution (deferred to v2).

</deferred>
