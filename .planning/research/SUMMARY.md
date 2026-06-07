# Project Research Summary

**Project:** OpenSRE
**Domain:** AI-driven SRE & Incident Investigation Platform
**Researched:** 2026-06-07
**Confidence:** HIGH

## Executive Summary

OpenSRE is designed to fill a critical gap in automated incident management. Traditional systems either alert humans (without context) or use LLMs to directly summarize alerts without checking actual metrics or logs (leading to hallucinations). OpenSRE implements a strict, evidence-first invariant: Evidence → Correlation → Timeline → Graph → Hypothesis → Ranking → Explanation.

To build OpenSRE as a production-grade open-source system, the architecture must support pluggability (for LLMs and Graph models), asynchronicity (non-blocking workers for querying external systems), and strict reproducibility (snapshots containing pipelines, ranking states, and model parameters).

Key risks include rate limiting or failure of external LLM APIs, scaling graph topologies in memory, and leakage of sensitive production credentials. These will be mitigated through a robust `LLMProvider` fallback router, abstracting the `GraphProvider` (facilitating easy Neo4j migration later), and writing a strict redaction layer during evidence normalization.

## Key Findings

### Recommended Stack

A Python 3.12 stack with FastAPI, Redis, and Celery provides the perfect balance of execution speed, dependency isolation, and background processing capability.

**Core technologies:**
- **Python 3.12 & FastAPI**: Core backend framework providing async endpoints and strong typing.
- **Redis & Celery**: Handles asynchronous, non-blocking execution of the investigation pipeline.
- **NetworkX**: In-memory graph library for modeling infrastructure topology and root cause analysis.
- **Pydantic v2**: Strict model validations for snapshots and reports.

### Expected Features

**Must have (table stakes):**
- **LLMProvider router**: Standarized interface supporting OpenAI, Anthropic, Gemini, Ollama, and OpenRouter.
- **Immutable Event Store**: Raw data storage for evidence collected during investigations.
- **Asynchronous Worker Queue**: Non-blocking enqueuing of runs returning Job IDs.
- **Investigation Snapshot & Audit Trail**: Full recording of actions and inputs.

**Should have (differentiators):**
- **Evidence Invariant Enforcement**: Refusal to output RCAs without linking to raw logs or metrics.
- **Explainable Confidence Factors**: Temporal alignment, evidence strength, source reliability, history similarity.
- **Multi-persona Explainer**: Role-based explanation generation (`sre`, `developer`, `executive`, `customer_support`).

**Defer (v2+):**
- **Neo4j Production Engine**: Persisted visual graph backend.
- **Real-time Streaming UI**: Web dashboard.
- **Auto-remediation execution**: Automated command running on clusters.

### Architecture Approach

The application follows a clean architecture pattern: API Layer → Application Services → Domain Layer → Providers/Integrations → Storage.

**Major components:**
1. **API & CLI Layer**: Triggers investigations and queries reports.
2. **InvestigationPipeline**: Background task coordinator executing collection, normalization, correlation, timeline sorting, graph modeling, hypothesis generation, ranking, and report writing.
3. **LLMProvider & GraphProvider Abstractions**: Decouple core domain logic from specific LLM models and graph databases.

### Critical Pitfalls

1. **Alert-to-LLM-to-Guess**: Bypassed evidence constraints lead to unreliable RCA reports. Avoided by strictly validating that all findings cite Event Store entries.
2. **Blocking API Handlers**: Long Prometheus/Loki queries block API threads. Avoided by delegating runs to Celery workers.
3. **Integration Coupling**: Hardcoding specific tools makes codebase fragile. Avoided by enforcing plugin SDK interfaces.

## Implications for Roadmap

The project will follow a 4-phase (Sprint-based) structure to build the core foundation before adding external integrations and advanced reasoning capabilities.

### Phase 1: Foundation (Sprint 1)
**Rationale:** Standardize routers, event schemas, workers, and testing infrastructure first to establish a solid platform core.
**Delivers:** LLMProvider, Event Store, Feature Flags, Audit Trail, InvestigationPipeline registry, Snapshots, IncidentReportV1 schema, Redis/Celery queue setup, Docker config, and pytest framework.
**Addresses:** Basic pipeline execution, multi-LLM routing, and async task processing.
**Avoids:** Blocking API Handlers.

### Phase 2: Integrations (Sprint 2)
**Rationale:** Add primary data collection targets once the pipeline execution engine is stable.
**Delivers:** Prometheus, Loki, Kubernetes, and GitHub connectors.
**Uses:** HTTPX and Kubernetes client packages.
**Implements:** The collection stage of the pipeline.

### Phase 3: Timeline & Correlation (Sprint 3)
**Rationale:** Organize raw data chronologically and identify logical relationships.
**Delivers:** TimelineBuilder (deterministic event sequencing) and Evidence Correlation engine.
**Addresses:** Normalization and correlation pipeline stages.

### Phase 4: Graph Engine & Root Cause Ranking (Sprint 4)
**Rationale:** Layer the NetworkX graph reasoning and multi-factor ranking algorithms on top of the sorted timeline.
**Delivers:** GraphProvider (NetworkX implementation), RootCauseRanker, and Synthetic Incident Testing suite.
**Avoids:** Un-Evidenced LLM RCA.

### Phase Ordering Rationale

- Pipeline logic is built in Phase 1 using mock/stub data sources before connecting to actual live APIs in Phase 2.
- Data sorting (Phase 3) must happen before Graph reasoning (Phase 4) because temporal relationships serve as inputs to topological root cause scoring.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Integrations):** Authenticating and securely retrieving logs/events across differing Kubernetes/Loki network setups requires API research.
- **Phase 4 (Graph Engine):** Topology modeling for NetworkX requires designing clear node/edge properties that map logical server dependencies.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard FastAPI and Celery configurations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Python, FastAPI, and Celery are mature and standard. |
| Features | HIGH | Requirements are explicitly defined in the OpenSRE specification. |
| Architecture | HIGH | Clean architecture patterns map cleanly to Python packages. |
| Pitfalls | HIGH | Standard SRE/AI pitfalls are well documented. |

**Overall confidence:** HIGH

### Gaps to Address

- **LLM Token Rate Limits:** Concurrent agent calls might trigger rate limits on public LLM endpoints. Resolved by building fallback routing and backoffs in LLMProvider.

## Sources

- OpenSRE specification prompt.
- FastAPI, Celery, and NetworkX documentation.

---
*Research completed: 2026-06-07*
*Ready for roadmap: yes*
