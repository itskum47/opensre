# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — v1.0 MVP

**Shipped:** 2026-06-07
**Phases:** 4 | **Plans:** 9 | **Sessions:** 2

### What Was Built
- Core API, `LLMProvider` router, Event Store, and async worker queue.
- Kubernetes status events, Prometheus metrics, Loki logs, and GitHub commit data source integrations.
- Timeline normalization and chronological event correlation engine with timezone-aware parsing.
- Service topology dependency map with NetworkX and multi-factor Root Cause Hypothesis Ranking.
- CLI investigate/explain subcommands and synthetic incident benchmarks verifying Redis saturation and DB outages.

### What Worked
- Custom `LLMProvider` and `FallbackLLMRouter` abstractions meant zero vendor SDK bloat and highly resilient mock/live execution.
- Timeline chronological sorting with timezone offset parsing prevented Naive vs Aware datetime subtract errors.
- Dynamic timezone-aware timestamp alignment in tests ensures event storms fall within the sliding correlation window.

### What Was Inefficient
- Initial Git commit keys were not extracted from messages, preventing automated correlation of change history events. Fixed by parsing commit descriptions in the timeline builder.

### Patterns Established
- Evidence-based incident reasoning order (Evidence -> Correlation -> Timeline -> Graph -> Hypothesis -> Ranking -> Explanation).
- SQLAlchemy immutable listeners preventing UPDATE/DELETE on AuditRecords.

### Key Lessons
1. Always enforce explicit evidence provenance for incident explanations rather than relying on direct LLM guesses.
2. Decouple third-party integrations with clean abstract classes (`DataSourcePlugin`, `GraphProvider`) to enable easy extension and mock validation.

### Cost Observations
- Model mix: 100% sonnet
- Sessions: 2
- Notable: Focused phase execution with no unnecessary dependency additions.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 2 | 4 | Initial OpenSRE MVP completion |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 21 | 100% | 0 |

### Top Lessons (Verified Across Milestones)

1. Enforce strict evidence provenance invariants before letting LLMs attempt explanation steps.
2. Design testing infrastructure with mock capabilities so verification executes reliably without requiring external cluster connectivity.
