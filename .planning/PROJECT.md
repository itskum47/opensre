# OpenSRE

## What This Is

OpenSRE is a production-grade open-source platform designed to investigate production incidents using alerts, metrics, logs, traces, deployments, Kubernetes state, Git repositories, runbooks, architecture documents, and historical incidents. It produces Root Cause Analysis (RCA), confidence scoring, evidence provenance, timeline reconstruction, blast radius analysis, recommended actions, and safe remediation plans.

## Core Value

An evidence-based incident reasoning engine that strictly enforces the invariant: Evidence → Correlation → Timeline → Graph → Hypothesis → Ranking → Explanation. It eliminates guesses by ensuring all findings are backed by verifiable evidence.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Multi-LLM Router (`LLMProvider`) supporting OpenAI, Anthropic, Gemini, Ollama, and OpenRouter
- [ ] Immutable Event Store under `backend/app/events/` for raw evidence persistence
- [ ] Pluggable Feature Flags (`ENABLE_MEMORY`, `ENABLE_REMEDIATION`, `ENABLE_MCP`, `ENABLE_SLACK`, `ENABLE_PAGERDUTY`)
- [ ] Immutable Audit Trail recording all investigation and system actions
- [ ] `InvestigationPipeline` executing sequential stages: collect, normalize, correlate, timeline, graph, hypothesize, rank, report
- [ ] Asynchronous worker queue (Redis + Celery or RQ) to process investigations without blocking the API
- [ ] Persistent investigation snapshots including raw events, timeline, graph, findings, report, and metadata
- [ ] Standardized `IncidentReportV1` schema shared across CLI, API, UI, and integrations
- [ ] Abstractions for infrastructure-dependent operations (e.g., `GraphProvider` supporting `NetworkXProvider` and `Neo4jProvider`)
- [ ] Automated evaluation harness and benchmark scenarios under `tests/benchmarks/` (e.g., redis_saturation, memory_leak, cpu_spike)
- [ ] Extensible Plugin SDK (`opensre_sdk/`) supporting plugins for DataSources, Agents, Graphs, and Remediation

### Out of Scope

- **Direct LLM Calls** — Prohibited. All LLM interactions must go through the `LLMProvider` abstraction.
- **Alert-to-LLM-to-Guess** — Invalid. LLMs are reasoning components, not sources of truth.
- **Sprint 1–4 UI Implementation** — Deferred. UI cannot be implemented until the core investigation engine and foundation are complete.
- **Slack & PagerDuty Integration in Sprint 1** — Deferred. Core engine must be validated first.
- **Memory before Synthetic Validation** — Deferred. System reasoning must be validated deterministically before enabling memory capabilities.
- **Tightly coupled optional features** — Optional features must remain decoupleable behind feature flags.

## Context

OpenSRE is designed as a pluggable, evidence-driven monorepo containing:
- `backend/`: FastAPI API, domain layer, application services, providers, event store
- `frontend/`: UI interface (deferred to post-Sprint 4)
- `cli/`: Command-line tool `opensre`
- `agents/`: Investigation agents
- `integrations/`: Tier 1 (Prometheus, Loki, OpenTelemetry, Kubernetes, GitHub), Tier 2, and Tier 3 sources
- `infra/`: Deployment configurations (Docker, etc.)
- `tests/`: Benchmarks and evaluation test suite
- `sdk/`: Extensible SDK (`opensre_sdk/`) for plugins

## Constraints

- **Evidence Requirement**: Every finding must contain explicit evidence. Loose finding descriptions without evidence are rejected.
- **Explainable Confidence**: All confidence scores must be explained using deterministic factors (temporal alignment, evidence strength, source reliability, historical similarity).
- **Reproducibility**: Snapshots must capture all metadata (schema_version, pipeline_version, ranking_version, graph_version, prompt_version, model, temperature) to allow full replay and regression testing.
- **Non-blocking API**: Investigation execution must be entirely asynchronous and queued via Celery/RQ + Redis.
- **Monorepo Structure**: All components (backend, frontend, CLI, SDK) must live in a unified monorepo.
- **Build order**: Must strictly follow the Sprint rules (Sprint 1: Router, Event Store, Feature Flags, Audit Trail, Pipeline, Snapshot, Report schema, Worker Queue, Docker, Tests).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Abstraction of LLM Provider | Prevent direct coupling to specific vendor SDKs and allow easy model swaps/routing. | — Pending |
| NetworkX for initial Graph Engine | Lightweight and fast memory-based graph analysis before moving to Neo4j. | — Pending |
| Redis + Celery/RQ for Worker Queue | Standard Python asynchronous task queue pattern for scalable, non-blocking jobs. | — Pending |
| FastAPI for Backend | Modern, fast web framework with strong support for asynchronous routing and typing. | — Pending |

---
*Last updated: 2026-06-07 after initialization*
