# Roadmap: OpenSRE

## Milestones

- ✅ **v1.0 MVP** - Phases 1-4 (shipped 2026-06-07)
- 🚧 **v1.1 Security & Advanced Features** - Phases 5-9 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) - SHIPPED 2026-06-07</summary>

### Phase 1: Foundation & Async Core
**Goal**: Core structures, LLM fallback router, Event Store, and Celery + Redis async worker.
**Plans**: 3 plans (Complete)

### Phase 2: System Integrations
**Goal**: Prometheus, Loki, Kubernetes API, and GitHub commit data source integration plugins.
**Plans**: 2 plans (Complete)

### Phase 3: Timeline & Correlation
**Goal**: Chronological timeline builder and sliding-window label-based event correlation.
**Plans**: 1 plan (Complete)

### Phase 4: Graph Engine & Root Cause Ranking
**Goal**: NetworkX service topology modeling, root cause multi-factor hypothesis ranker, benchmarks, and CLI.
**Plans**: 3 plans (Complete)

</details>

### 🚧 v1.1 Security & Advanced Features (In Progress)

**Milestone Goal:** Implement notification systems, Neo4j persistent graph storage, historical memory RCA learning, human-in-the-loop remediation, and a web-based dashboard UI.

#### Phase 5: Neo4j Storage Layer
**Goal**: Implement persistent graph database layer to store service topology, incident graphs, and run dependency path queries.
**Depends on**: Phase 4
**Requirements**: [NEO4-01, NEO4-02]
**Success Criteria** (what must be TRUE):
  1. Incident and dependency graphs can be successfully saved to and loaded from a Neo4j database.
  2. Shared dependencies and path tracing queries can be run across concurrent investigations.
**Plans**: 2 plans
- [ ] 05-01: Neo4j database connection pool, configuration, and basic Node/Edge schema sync.
- [ ] 05-02: Neo4j GraphProvider implementation with query API extensions for shared dependency tracing.

#### Phase 6: Slack & PagerDuty Notifications
**Goal**: Add alert integrations with Slack (including Block Kit interactive approvals) and PagerDuty (including bidirectional status sync).
**Depends on**: Phase 5
**Requirements**: [NOTF-01, NOTF-02, NOTF-03, NOTF-04]
**Success Criteria** (what must be TRUE):
  1. Slack alerts are posted to a channel with Block Kit interactive buttons on investigation start, transitions, and completion.
  2. PagerDuty incidents are automatically acknowledged and resolved based on investigation status.
  3. Webhook endpoints verify Slack/PagerDuty signatures and update incident notes/states accordingly.
**Plans**: 2 plans
- [ ] 06-01: Slack bot client, Block Kit message builders, webhook endpoints, and signing signature verification.
- [ ] 06-02: PagerDuty client with incident state sync, status sync handlers, and notes attachment.

#### Phase 7: Historical Incident Memory
**Goal**: Implement SQLite BLOB vector storage and cosine similarity lookups to recommend past remediation plans.
**Depends on**: Phase 6
**Requirements**: [MEM-01, MEM-02]
**Success Criteria** (what must be TRUE):
  1. Incident report data can be serialized, converted to vector embeddings, and stored as SQLite BLOBs.
  2. Cosine similarity search successfully retrieves similar historical incidents to adjust hypothesis ranking and suggest remediation.
**Plans**: 2 plans
- [ ] 07-01: SQLite vector storage schema, serialization methods, and embedding generation helpers.
- [ ] 07-02: Cosine similarity algorithm implementation and `RootCauseRanker` adjustment to suggest remediation plans.

#### Phase 8: Human-in-the-Loop Remediation
**Goal**: Develop stateful approval workflow for remediation scripts with execution cooldowns and health validation.
**Depends on**: Phase 7
**Requirements**: [REMED-01, REMED-02]
**Success Criteria** (what must be TRUE):
  1. Remediation scripts are held in `PENDING_APPROVAL` and require manual confirmation via Slack/API.
  2. Approved scripts execute asynchronously, checking cooldown limits first, followed by automated post-remediation validation health checks.
**Plans**: 2 plans
- [ ] 08-01: Remediation service state machine, safety checks, execution endpoints, and Slack webhook approval routing.
- [ ] 08-02: Celery asynchronous worker task for remediation, cooldown timers, and automated validation checking.

#### Phase 9: Web Dashboard UI
**Goal**: Build visual Vite + React UI dashboard to list investigations, view timelines, and explore dependency graphs.
**Depends on**: Phase 8
**Requirements**: [UI-01, UI-02]
**Success Criteria** (what must be TRUE):
  1. Users can list investigations, view chronological interactive timelines, and trigger manual investigations from the UI.
  2. The UI renders an interactive D3 force-directed dependency graph blast-radius explorer highlighting suspected root causes.
**Plans**: 2 plans
- [ ] 09-01: Vite React scaffolding, API client integrations, investigation listing, and interactive timelines.
- [ ] 09-02: Interactive D3 dependency graph blast-radius rendering, integration with root cause data, and dashboard visual polish.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Async Core | v1.0 | 3/3 | Complete | 2026-06-07 |
| 2. System Integrations | v1.0 | 2/2 | Complete | 2026-06-07 |
| 3. Timeline & Correlation | v1.0 | 1/1 | Complete | 2026-06-07 |
| 4. Graph Engine & Root Cause Ranking | v1.0 | 3/3 | Complete | 2026-06-07 |
| 5. Neo4j Storage Layer | 2/2 | Complete    | 2026-06-08 | - |
| 6. Slack & PagerDuty Notifications | v1.1 | 0/2 | Not started | - |
| 7. Historical Incident Memory | v1.1 | 0/2 | Not started | - |
| 8. Human-in-the-Loop Remediation | v1.1 | 0/2 | Not started | - |
| 9. Web Dashboard UI | v1.1 | 0/2 | Not started | - |
