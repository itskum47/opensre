# Requirements: OpenSRE

**Defined:** 2026-06-08
**Core Value:** Evidence-based incident reasoning engine that strictly enforces the Evidence → Correlation → Timeline → Graph → Hypothesis → Ranking → Explanation order.

## v1.1 Requirements

### Notifications & Alerting
- [ ] **NOTF-01**: The system must integrate Slack notifications to post channel alerts on investigation starts, transitions, and completions.
- [ ] **NOTF-02**: The system must integrate PagerDuty to automatically acknowledge and resolve alerts in sync with OpenSRE investigation states.
- [ ] **NOTF-03**: The system must support Slack interactive blocks (Block Kit) for manual approval of proposed remediation scripts.
- [ ] **NOTF-04**: The system must support bidirectional sync with PagerDuty, appending OpenSRE timelines and root cause findings as incident notes.

### Persistent Graph Engine
- [ ] **NEO4-01**: The system must implement a `Neo4jProvider` conforming to the `GraphProvider` interface to persist incident and topology graphs.
- [ ] **NEO4-02**: The graph engine must support running path tracing queries across concurrent investigations to identify shared dependencies.

### Incident Memory
- [ ] **MEM-01**: The system must implement an incident memory engine storing/querying vector embeddings in SQLite via cosine similarity to match historical incident patterns.
- [ ] **MEM-02**: The memory engine must automatically suggest successful past remediation plans when a similar incident profile is identified.

### Human-in-the-Loop Remediation
- [ ] **REMED-01**: The system must support stateful human-approved remediation script execution, requiring explicit webhook or UI approval before running commands.
- [ ] **REMED-02**: The remediation system must trigger automated post-remediation health validation checks to verify if the alert has cleared.

### Dashboard UI
- [ ] **UI-01**: The system must build a web-based dashboard UI to trigger investigations, list past runs, and view interactive chronological timelines.
- [ ] **UI-02**: The dashboard UI must render an interactive D3 force-directed dependency graph blast-radius explorer highlighting suspected root causes.

## Future Requirements
- **REMED-03**: Autonomous self-healing without human intervention (gated on safety thresholds).

## Out of Scope
- **Multi-region Neo4j clustering** — Overkill for v1.1. Single-instance database deployment is sufficient.
- **Fully autonomous execution** — All remediation actions must require explicit human confirmation.
- **Replacing SQLite as transactional DB** — Neo4j is purely for dependency graph analysis; system metadata remains in SQLite.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NEO4-01 | Phase 5 | Pending |
| NEO4-02 | Phase 5 | Pending |
| NOTF-01 | Phase 6 | Pending |
| NOTF-02 | Phase 6 | Pending |
| NOTF-03 | Phase 6 | Pending |
| NOTF-04 | Phase 6 | Pending |
| MEM-01 | Phase 7 | Pending |
| MEM-02 | Phase 7 | Pending |
| REMED-01 | Phase 8 | Pending |
| REMED-02 | Phase 8 | Pending |
| UI-01 | Phase 9 | Pending |
| UI-02 | Phase 9 | Pending |

**Coverage:**
- v1.1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-08*
*Last updated: 2026-06-08 after v1.1 scoping and approval*
