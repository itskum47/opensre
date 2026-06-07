# Roadmap: OpenSRE

## Overview

This roadmap defines the implementation path for OpenSRE, a production-grade AI incident investigation engine. The journey goes from ensembling the core framework and worker queue (Phase 1), through connecting live integrations (Phase 2), sorting and correlating evidence chronologically (Phase 3), and finally modeling dependencies via graphs to run confidence-ranked RCA (Phase 4).

## Phases

- [ ] **Phase 1: Foundation (Sprint 1)** - Create the backend core, LLMProvider router, Worker queue, Snapshots, and Docker test setup.
- [ ] **Phase 2: Integrations (Sprint 2)** - Implement Prometheus, Loki, Kubernetes, and GitHub connectors.
- [ ] **Phase 3: Timeline & Correlation (Sprint 3)** - Implement TimelineBuilder and correlation engine.
- [ ] **Phase 4: Graph Engine & Root Cause Ranking (Sprint 4)** - Model system topology, rank root causes, and run evaluation benchmarks.

## Phase Details

### Phase 1: Foundation (Sprint 1)
**Goal**: Establish the Core API, LLMProvider abstraction, Event Store, Feature Flags, Audit Trail, async Workers, and Docker/CI-CD environment.
**Depends on**: Nothing
**Requirements**: ROUT-01, ROUT-02, ROUT-03, STOR-01, STOR-02, FLAG-01, AUDT-01, PIPE-01, PIPE-02, SNAP-01, SNAP-02, REPT-01, WORK-01, WORK-02, DOCK-01, DOCK-02
**Success Criteria** (what must be TRUE):
  1. API endpoint `POST /investigations` returns a `job_id` asynchronously under 50ms without blocking.
  2. Celery/RQ workers execute `InvestigationPipeline` stages sequentially, updating states from QUEUED to COMPLETED in the registry.
  3. Investigation snapshots and audit trail logs are persisted immutably in SQLite/PostgreSQL and the local event store.
  4. Multi-LLM calls route successfully through `LLMProvider` adapters without direct imports of SDKs outside `providers/`.
  5. CI/CD configuration (GitHub Actions or GitLab CI) successfully executes testing, linting, and style formatting checks.
**Plans**: 3 plans

Plans:
- [ ] 01-01: Setup monorepo, config, and `LLMProvider` router.
- [ ] 01-02: Develop `InvestigationPipeline`, Event Store, Audit Trail, and async worker queue.
- [ ] 01-03: Create snapshot writer, `IncidentReportV1` schemas, Docker setup, CI/CD pipeline configs, and basic pytest suite.

### Phase 2: Integrations (Sprint 2)
**Goal**: Build plugins to fetch data from Kubernetes, Prometheus, Loki, and GitHub.
**Depends on**: Phase 1
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04
**Success Criteria** (what must be TRUE):
  1. K8s status events are queried and stored in the Event Store.
  2. Metrics from Prometheus and logs from Loki are fetched for investigation time-ranges.
  3. GitHub commits are retrieved and indexed as potential deployment events.
**Plans**: 2 plans

Plans:
- [ ] 02-01: Implement Kubernetes, Prometheus, and Loki integrations.
- [ ] 02-02: Implement GitHub connector integration.

### Phase 3: Timeline & Correlation (Sprint 3)
**Goal**: Normalize raw collected events into a single, correlated chronological timeline.
**Depends on**: Phase 2
**Requirements**: TIME-01, CORR-01
**Success Criteria** (what must be TRUE):
  1. Incident events are sorted chronologically and normalized under a unified schema.
  2. Events from different logs/metrics/commits are correlated based on timestamps and labels.
**Plans**: 1 plan

Plans:
- [ ] 03-01: Build `TimelineBuilder` and the Evidence Correlation engine.

### Phase 4: Graph Engine & Root Cause Ranking (Sprint 4)
**Goal**: Construct service topology using NetworkX, rank hypotheses with explainable factors, build CLI/SDK, and run benchmarks.
**Depends on**: Phase 3
**Requirements**: GRP-01, GRP-02, RNK-01, RNK-02, TEST-01, TEST-02, CLI-01, CLI-02, SDK-01
**Success Criteria** (what must be TRUE):
  1. Incident dependencies are modeled dynamically using `NetworkXProvider`.
  2. Root cause ranker calculates hypothesis confidence using temporal, evidence, source, and history factors.
  3. CLI commands `opensre investigate` and `opensre explain` produce accurate, persona-based RCA narratives.
  4. Benchmark evaluations report accurate scores for redis_saturation and database_outage.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Implement `GraphProvider` (NetworkX) and the `RootCauseRanker`.
- [ ] 04-02: Develop CLI commands and the plugin SDK interfaces.
- [ ] 04-03: Run synthetic incident testing and verify baseline benchmark coverage.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation (Sprint 1) | 0/3 | Not started | - |
| 2. Integrations (Sprint 2) | 0/2 | Not started | - |
| 3. Timeline & Correlation (Sprint 3) | 0/1 | Not started | - |
| 4. Graph Engine & Root Cause Ranking (Sprint 4) | 0/3 | Not started | - |
