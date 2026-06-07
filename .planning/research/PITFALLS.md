# Pitfalls Research

**Domain:** AI-driven SRE & Incident Investigation Platform
**Researched:** 2026-06-07
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Un-Evidenced LLM RCA (Alert -> LLM -> Guess)

**What goes wrong:**
The LLM is prompted directly with a raw alert and summarizes a generic root cause. The user acts on it, but the analysis is wrong (hallucinated), potentially worsening the outage.

**Why it happens:**
It is easier and faster to just wrap an alert string in an LLM call instead of constructing a unified timeline, querying service dependency graphs, and linking metrics/logs.

**How to avoid:**
Enforce the Evidence Invariant (Rule 2). The system must collect, normalize, and correlate raw metrics/logs/commits before asking the LLM to hypothesize. The LLM must reason *over* the compiled timeline and graph, and must cite specific events in the Event Store.

**Warning signs:**
Empty evidence fields in findings or incident reports. High rate of incorrect RCAs on synthetic benchmarks.

**Phase to address:**
Phase 1: Foundation (Pipeline & Snapshot validation).

---

### Pitfall 2: Tightly Coupled Integrations

**What goes wrong:**
Adding a new metric/log source (e.g. Datadog instead of Prometheus) requires rewriting the core investigation pipeline logic.

**Why it happens:**
Developers directly import integration clients (like Prometheus API client) inside the pipeline execution stages instead of using a DataSource abstraction.

**How to avoid:**
Define a `DataSourcePlugin` interface in the Plugin SDK. All metrics, logs, and trace collection must be handled by classes implementing this interface.

**Warning signs:**
Core domain files importing `kubernetes` or `prometheus_api_client`.

**Phase to address:**
Phase 2: Integrations.

---

### Pitfall 3: Blocking API Handlers

**What goes wrong:**
When a user requests an investigation, the API waits synchronously while the system queries Prometheus, Loki, K8s, and runs LLM models, leading to request timeouts.

**Why it happens:**
Directly executing `pipeline.run()` inside FastAPI routes rather than enqueuing a job in Celery/RQ.

**How to avoid:**
All investigation requests must return a `job_id` immediately with status `QUEUED`. Workers run the pipeline asynchronously.

**Warning signs:**
API request latency exceeds 500ms on investigation triggers.

**Phase to address:**
Phase 1: Foundation.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| In-memory Graph State | Easy setup, no database required. | Cannot scale graph sizes or query historical topologies easily. | Greenfield phase (Phase 1/2) using NetworkX. Must migrate to Neo4j later. |
| Local File-system Event Store | Avoids configuring S3/PostgreSQL. | Disk usage grows, not suitable for multi-worker container scaling. | Sprint 1 local development. Must support AWS S3 or database adapters in v2. |
| In-memory Feature Flags | Fast to build, zero dependencies. | Requires server restarts to change feature flags. | Sprint 1. Must use config files or env vars later. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Prometheus | Querying with static time ranges. | Use the investigation start/end times dynamically, adding buffers. |
| Kubernetes | Assuming K8s events are kept forever. | Handle missing events gracefully; K8s deletes events after ~1 hour. |
| Loki | Querying massive time windows with generic regex. | Narrow down search query using localized service labels. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Giant Trace Collection | Worker memory exhaustion. | Limit trace size per service/run. | High traffic incidents (>1000 spans/sec). |
| Parallel LLM Rate Limits | API errors or slow retries. | Implement token bucketing, retry backoffs, and fallback providers. | Multi-agent pipelines running concurrent stages. |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing Secrets in Reports | Raw logs inside report contain API keys or auth tokens. | Implement a regex-based redaction filter in the normalize stage. |
| LLM Command Injection | System queries git repositories and feeds arbitrary files into LLMs without sandboxing, allowing remote code execution if the LLM executes prompts found in code. | Never allow the LLM to construct commands that are directly executed on host machine. |

## "Looks Done But Isn't" Checklist

- [ ] **Multi-LLM Router:** Often missing error-handling for provider downtime — verify fallbacks work.
- [ ] **Asynchronous Workers:** Often fails on tasks when worker gets restarted mid-run — verify task state persistence.
- [ ] **Event Store:** Often allows raw event mutation in test scenarios — verify file/DB write-once rules.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| LLM Rate Limiting | LOW | Check provider status, configure secondary providers (OpenRouter/Ollama), verify exponential backoff is active. |
| Database Lockups | MEDIUM | Add connection pooling and transaction timeouts in SQLAlchemy configurations. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Un-Evidenced LLM RCA | Phase 1 | Run synthetic benchmarks and assert that `report.evidence` is not empty. |
| Tightly Coupled Integrations | Phase 2 | Ensure all integrations implement the `DataSourcePlugin` abstract interface. |
| Blocking API Handlers | Phase 1 | Write an integration test that calls POST `/investigations` and asserts response time is < 50ms. |

## Sources

- SRE best practices.
- AI system design postmortems.

---
*Pitfalls research for: OpenSRE*
*Researched: 2026-06-07*
