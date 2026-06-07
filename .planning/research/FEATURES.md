# Feature Research

**Domain:** AI-driven SRE & Incident Investigation Platform
**Researched:** 2026-06-07
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-LLM Router | Ability to run investigations on various LLM backends. | MEDIUM | Standardized `LLMProvider` interface. |
| Event Store | Immutable record of raw metrics/logs/traces collected. | LOW | Essential for provenance, replay, and validation. |
| Investigation Pipeline | Sequential stages: collect, normalize, correlate, timeline, graph, hypothesize, rank, report. | HIGH | Core logic that organizes reasoning. |
| Incident Report (v1 Schema) | Clear, JSON-based incident summary, RCA, timeline, evidence. | LOW | Standard structure shared by API, CLI, and integrations. |
| Worker Queue | Non-blocking asynchronous task execution. | MEDIUM | Running investigations via background tasks. |
| CLI Tool | Local command-line tool to run investigations. | MEDIUM | `opensre investigate <file>` and `opensre explain <id>`. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Evidence Invariant | Guarantees that every finding has explicit verifiable logs, metrics, or commits attached. | HIGH | Prevents LLM hallucinations. |
| Explainable Confidence | Broken down into factors (temporal, evidence, source, history) rather than arbitrary percentages. | MEDIUM | Builds user trust. |
| Graph Engine RCA | NetworkX-based model of dependencies (services, databases, infra) to find exact root causes. | HIGH | Moves beyond simple log grep to system topology reasoning. |
| Multi-persona Explainer | SRE vs Developer vs Executive vs Support explanations. | MEDIUM | Adaptable narrative generation based on user role. |
| Extensible Plugin SDK | Allows developers to write their own data sources, agents, or graph routers. | HIGH | Encourages ecosystem growth. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Alert → LLM → Guess | Fast to build, quick demo appeal. | Hallucinates, zero reproducibility, unreliable for production. | Enforce Evidence → Correlation → Timeline → Graph. |
| Real-time Streaming UI | Cool visual dashboard. | High overhead, complex UI state management in early phases. | Static snapshot generation and REST-based polling. |
| Automatic Auto-Remediation | Wants AI to automatically fix production bugs. | Risk of cascading outages, security vulnerabilities. | Human-in-the-loop: suggest safe remediation, manual approval. |

## Feature Dependencies

```
[InvestigationPipeline]
    └──requires──> [Event Store]
                        └──requires──> [Feature Flags]

[Graph Engine] ──enhances──> [InvestigationPipeline]
[Root Cause Ranker] ──enhances──> [InvestigationPipeline]
[Explain Persona Command] ──requires──> [InvestigationPipeline]
```

### Dependency Notes

- **InvestigationPipeline requires Event Store**: The pipeline cannot process stages without consuming from or writing to the immutable Event Store.
- **Graph Engine enhances InvestigationPipeline**: Graph-based topology models improve RCA ranking accuracy.
- **Explain Persona Command requires InvestigationPipeline**: Cannot generate persona explanations without a completed investigation snapshot and report.

## MVP Definition

### Launch With (v1 - Sprint 1)

Minimum viable product — what's needed to validate the concept.

- [ ] **Multi-LLM Router** — Unified LLMProvider to query models (OpenAI, Anthropic, Gemini, Ollama, OpenRouter).
- [ ] **Immutable Event Store** — Local JSON-based files under `backend/app/events/`.
- [ ] **Feature Flags** — Ability to toggle capabilities (`ENABLE_MEMORY`, `ENABLE_REMEDIATION`, etc.).
- [ ] **Investigation Pipeline & Registry** — Pipeline tracking from QUEUED to COMPLETED.
- [ ] **Worker Queue** — Async runner using Celery/RQ + Redis.
- [ ] **Investigation Snapshot & ReportV1** — Outputs containing schema, findings, and metadata.
- [ ] **Test Harness** — Baseline benchmark runner to evaluate results.

### Add After Validation (v1.x - Sprint 2 & 3)

Features to add once core is working.

- [ ] **Tier 1 Integrations** — Prometheus, Loki, Kubernetes, GitHub.
- [ ] **Timeline Engine** — Order events deterministically.
- [ ] **Evidence Correlation** — Correlate events across sources.

### Future Consideration (v2+ - Sprint 4 & Beyond)

Features to defer until product-market fit is established.

- [ ] **Graph Engine** — NetworkX model for dependencies.
- [ ] **Root Cause Ranker** — Multi-factor hypothesis ranking.
- [ ] **Explain command** — Persona-based command line.
- [ ] **Plugin SDK** — Extensibility interfaces.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| LLM Router | HIGH | MEDIUM | P1 |
| Event Store | HIGH | LOW | P1 |
| Pipeline & Snapshots | HIGH | HIGH | P1 |
| Worker Queue | HIGH | MEDIUM | P1 |
| Tier 1 Integrations | HIGH | HIGH | P2 |
| Timeline & Correlation | HIGH | MEDIUM | P2 |
| Graph Engine & RCA | HIGH | HIGH | P3 |
| SDK & Persona Explainers | MEDIUM | HIGH | P3 |

## Competitor Feature Analysis

| Feature | Competitor A (PagerDuty Runbook Gen) | Competitor B (Dynatrace Davis AI) | Our Approach |
|---------|--------------------------------------|-----------------------------------|--------------|
| LLM Usage | Direct prompt on alerts. | Internal closed AI model. | Abstraction layer, multi-LLM, evidence-only. |
| Evidence | None, text summaries. | Proprietary metrics only. | Strict evidence invariant schema. |
| Pluggability | Closed integrations. | Heavy agent install. | Lightweight SDK plugins, open monorepo. |

## Sources

- OpenSRE specification.
- Common SRE postmortems and RCA expectations.

---
*Feature research for: OpenSRE*
*Researched: 2026-06-07*
