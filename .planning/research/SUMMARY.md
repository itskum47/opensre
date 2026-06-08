# Project Research Summary

**Project:** OpenSRE
**Domain:** Incident Investigation & Reason Engine (SRE)
**Researched:** 2026-06-07
**Confidence:** HIGH

## Executive Summary

To scale OpenSRE from a single-machine CLI tool (v1.0 MVP) to a production-grade enterprise platform, milestone v1.1 introduces persistent graph storage (Neo4j), real-time alerts (Slack & PagerDuty), historical incident learning (Memory), human-approved remediation, and a visual dashboard UI.

The recommended approach enforces our core Evidence-based invariant while adding safe notifications and persistent graph queries. The primary risk is database coupling and unauthenticated action approval webhooks, which we mitigate through interface decoupling and HMAC signature verification.

## Key Findings

### Recommended Stack

We recommend official, modern, and thread-safe Python SDKs for Neo4j, Slack, and PagerDuty, along with a lightweight in-memory/SQLite approach for vector search to avoid deployment bloat.

**Core technologies:**
- `neo4j` (v5.x+): Persists dependency graphs and allows running graph algorithms — replacing deprecated `neo4j-driver`.
- `slack-sdk` (v3.42.0+): Real-time alerts and interactive approvals via Block Kit — replacing deprecated `slackclient`.
- `pagerduty` (v1.0.0+): Bidirectional incident acknowledgement and sync — replacing deprecated `pdpyras`.
- SQLite BLOB + Cosine Similarity: Stores and searches historical incident embeddings with zero external infrastructure footprint.
- React + Vite + Vanilla CSS: Builds a premium, high-performance visual dashboard.

### Expected Features

**Must have (table stakes):**
- Slack/PagerDuty alerts triggered on investigation start/finish.
- Graph persistence into a Neo4j database.
- Vector similarity search against historical incident reports.
- UI listing investigations with interactive timelines.

**Should have (competitive):**
- Slack Thread updates representing active pipeline stage transitions.
- Interactive block approvals to execute remediation scripts.
- PageRank and centrality analysis on Neo4j topology.
- Visual blast-radius D3 visualization in the dashboard.

**Defer (v2+):**
- Multi-region Neo4j clustering.
- Automated remediation execution without any human-in-the-loop validation.

### Architecture Approach

The architecture extends the pipeline with decoupled provider interfaces and safe approval middleware.

**Major components:**
1. `Neo4jProvider`: Graph persistence database adapter.
2. `NotificationRouter`: Dispatches alerts to Slack Bot client and PagerDuty REST client.
3. `IncidentMemoryEngine`: Manages sqlite vector storage and similarity searches.
4. `RemediationOrchestrator`: Asynchronous Celery approval runner.
5. FastAPI Webhook Middleware: Validates Slack webhook signatures.

### Critical Pitfalls

1. **Hard coupling to Neo4j** — Avoid by wrapping Neo4j operations in try-except and falling back gracefully to NetworkX.
2. **Unauthenticated Approve Actions** — Avoid by strictly verifying HMAC SHA256 signatures for incoming Slack webhook web requests.
3. **Infinite Remediation Loops** — Avoid by adding a resource-level execution cooldown (e.g. 1 hour).
4. **Graph visualization lag** — Avoid by filtering dashboard graph rendering to 3 hops maximum from the root cause node.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 5: Neo4j Storage Layer
**Rationale:** Establishing persistent graph storage is a core backend dependency for query APIs and UI visualization.
**Delivers:** `Neo4jProvider` integration, node/edge sync, fallback handlers.
**Addresses:** `NEO4-01`
**Avoids:** Hard coupling to Neo4j.

### Phase 6: Slack & PagerDuty Notifications
**Rationale:** Connects pipeline state updates to standard alerting systems, enabling immediate user visibility.
**Delivers:** Slack WebClient, Block Kit message builders, PagerDuty Client, and webhook signature verification middleware.
**Addresses:** `NOTF-01`, `NOTF-02`
**Avoids:** Unauthenticated approval actions.

### Phase 7: Historical Incident Memory
**Rationale:** Incident similarities must be computed and indexed before the remediation orchestrator can suggest past successful actions.
**Delivers:** SQLite vector storage, cosine similarity search inside `RootCauseRanker`.
**Addresses:** `MEM-01`
**Avoids:** Memory similarity drift.

### Phase 8: Human-in-the-Loop Remediation
**Rationale:** Integrates safety boundaries and Celery worker executions once notification webhooks and memory indexes exist.
**Delivers:** `RemediationOrchestrator`, approval status state machine, cooldown gates, and automated post-check triggers.
**Addresses:** `REMED-01`
**Avoids:** Infinite remediation loops.

### Phase 9: Web Dashboard UI
**Rationale:** Visualizes timelines, graph blast radiuses, and remediation status screens implemented in all prior backend phases.
**Delivers:** Vite React SPA with timeline, D3 graph layout, and pipeline state viewer.
**Addresses:** `UI-01`
**Avoids:** Graph visualization browser lag.

### Phase Ordering Rationale

- Graph and notification layers come first to establish persistent telemetry and alerting channels.
- Memory index runs next to build the historical database before the remediation service starts query-matching.
- Remediation runs fourth, utilizing the Slack interactive blocks and Memory engine suggestions.
- UI runs last as it aggregates all backend capabilities into a cohesive, premium visualization interface.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 8 (Remediation):** Verification of shell environments and container execution sandbox safety.
- **Phase 9 (UI):** D3 force layout rendering tuning to prevent high browser CPU overhead.

Phases with standard patterns (skip research-phase):
- **Phase 5 (Neo4j):** Official `neo4j` Python driver has standardized connection pooling patterns.
- **Phase 6 (Notifications):** Slack SDK and PagerDuty SDK have extremely well-documented client protocols.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Validated modern libraries and verified deprecations. |
| Features | HIGH | Table stakes and competitive requirements mapped. |
| Architecture | HIGH | Visual dataflow and integration hooks identified. |
| Pitfalls | HIGH | Specific mitigations designed for security and safety. |

**Overall confidence:** HIGH

### Gaps to Address

- **Slack Block Kit Sandbox**: Testing Slack webhooks locally requires an ngrok tunnel or equivalent forwarding mechanism.
- **Mock PagerDuty Endpoint**: Standard unit testing requires a mock client for PagerDuty REST API routes.

## Sources

### Primary (HIGH confidence)
- `neo4j` PyPI: Neo4j official Python package references.
- `slack-sdk` Docs: Slack python integration guide and request signing.
- `pagerduty` PyPI: Official PagerDuty Python client details.

---
*Research completed: 2026-06-07*
*Ready for roadmap: yes*
