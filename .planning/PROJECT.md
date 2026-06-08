# OpenSRE

## What This Is

OpenSRE is a production-grade open-source platform designed to investigate production incidents using alerts, metrics, logs, traces, deployments, Kubernetes state, Git repositories, runbooks, architecture documents, and historical incidents. It produces Root Cause Analysis (RCA), confidence scoring, evidence provenance, timeline reconstruction, blast radius analysis, recommended actions, and safe remediation plans.

## Core Value

An evidence-based incident reasoning engine that strictly enforces the invariant: Evidence → Correlation → Timeline → Graph → Hypothesis → Ranking → Explanation. It eliminates guesses by ensuring all findings are backed by verifiable evidence.

## Current Milestone: v1.1 Security & Advanced Features

**Goal:** Implement notification systems, Neo4j persistent graph storage, historical memory RCA learning, human-in-the-loop remediation, and a web-based dashboard UI.

**Target features:**
- Slack notifications and interactive blocks
- PagerDuty alerting and incident status sync
- Neo4j persistent graph storage and visualization
- Historical incident memory-based RCA learning
- Human-in-the-loop remediation orchestration
- Web-based dashboard UI

## Requirements

### Validated

- ✓ ROUT-01, ROUT-02, ROUT-03: Multi-LLM Router (`LLMProvider`) supporting OpenAI, Anthropic, Gemini, Ollama, and OpenRouter without vendor coupling.
- ✓ STOR-01, STOR-02: Immutable raw Event Store under `backend/app/events/` for evidence persistence.
- ✓ FLAG-01: Pluggable Feature Flags (`ENABLE_MEMORY`, `ENABLE_REMEDIATION`, `ENABLE_MCP`, `ENABLE_SLACK`, `ENABLE_PAGERDUTY`).
- ✓ AUDT-01: Immutable Audit Trail database logging all pipeline status transitions.
- ✓ PIPE-01, PIPE-02: `InvestigationPipeline` executing sequential stages (collect, normalize, correlate, timeline, graph, hypothesize, rank, report) and registry state tracking.
- ✓ SNAP-01, SNAP-02: Persistent investigation snapshots with extensive metadata.
- ✓ REPT-01: Standardized `IncidentReportV1` schema.
- ✓ WORK-01, WORK-02: Non-blocking background worker queue processing via Celery and Redis.
- ✓ DOCK-01, DOCK-02: Docker / Compose configurations and dual-CI configurations (GitHub Actions and GitLab CI).
- ✓ INTG-01, INTG-02, INTG-03, INTG-04: Prometheus, Loki, Kubernetes API, and GitHub commit data source integrations.
- ✓ TIME-01, CORR-01: Chronological timeline compilation and sliding-window label-based event correlation.
- ✓ GRP-01, GRP-02: `GraphProvider` abstraction with directed in-memory `NetworkXProvider` implementation.
- ✓ RNK-01, RNK-02: Multi-factor `RootCauseRanker` with explainable confidence scoring.
- ✓ TEST-01, TEST-02: Synthetic incident benchmark test suite evaluating Redis memory saturation and database outages.
- ✓ CLI-01, CLI-02: `opensre` CLI tool supporting `investigate` and `explain` subcommands.
- ✓ SDK-01: Decoupled plugin interfaces.

### Active

- [ ] **NOTF-01**: Integrate Slack notifications and interactive blocks for real-time investigation alerts.
- [ ] **NOTF-02**: Integrate PagerDuty alerting, incident acknowledgements, and status synchronization.
- [ ] **NEO4-01**: Implement `Neo4jProvider` for persistent database graph storage and visualization.
- [ ] **MEM-01**: Implement memory-based learning from historical incidents to enhance RCA similarity ranking (`ENABLE_MEMORY`).
- [ ] **REMED-01**: Implement human-in-the-loop remediation orchestration (`ENABLE_REMEDIATION`).
- [ ] **UI-01**: Build a web-based dashboard UI to trigger investigations, visualize timelines, and render dependency graphs.

### Out of Scope

- **Direct LLM Calls** — Prohibited. All LLM interactions must go through the `LLMProvider` abstraction.
- **Alert-to-LLM-to-Guess** — Invalid. LLMs are reasoning components, not sources of truth.
- **Automatic Auto-Remediation without approval** — Security and stability risk. Only human-approved remediation workflows are considered.

## Context

OpenSRE is designed as a pluggable, evidence-driven monorepo containing:
- `backend/`: FastAPI API, domain layer, application services, providers, event store
- `frontend/`: UI interface (deferred to v1.1+)
- `cli/`: Command-line tool `opensre`
- `sdk/`: Extensible SDK for plugins
- Shipped v1.0 MVP with 2,400+ LOC in Python. Tech stack: FastAPI, SQLAlchemy, SQLite, Celery, Redis, NetworkX, Pytest.

## Constraints

- **Evidence Requirement**: Every finding must contain explicit evidence. Loose finding descriptions without evidence are rejected.
- **Explainable Confidence**: All confidence scores must be explained using deterministic factors (temporal alignment, evidence strength, source reliability, historical similarity).
- **Reproducibility**: Snapshots must capture all metadata to allow full replay and regression testing.
- **Non-blocking API**: Investigation execution must be entirely asynchronous and queued via Celery + Redis.
- **Monorepo Structure**: All components live in a unified monorepo.
- **CI/CD Execution**: Automated testing and verification pipelines must run on GitHub Actions or GitLab CI.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Abstraction of LLM Provider | Prevent direct coupling to specific vendor SDKs and allow easy model swaps/routing. | ✓ Good |
| NetworkX for initial Graph Engine | Lightweight and fast memory-based graph analysis before moving to Neo4j. | ✓ Good |
| Redis + Celery for Worker Queue | Standard Python asynchronous task queue pattern for scalable, non-blocking jobs. | ✓ Good |
| FastAPI for Backend | Modern, fast web framework with strong support for asynchronous routing and typing. | ✓ Good |
| GitHub Actions / GitLab CI for CI/CD | Standardized open-source automation platforms to run linting and tests. | ✓ Good |
| Git Commit Key Correlation | Parse commit messages for service names to align change history with corresponding pods. | ✓ Good |

---
*Last updated: 2026-06-07 after v1.1 milestone started*
