# Stack Research

**Domain:** AI-driven SRE & Incident Investigation Platform
**Researched:** 2026-06-07
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Core Programming Language | Strong ecosystem for data structures, AI/LLM libraries, graph reasoning, and backend services. |
| FastAPI | 0.111.0 | Backend REST API Framework | Extremely fast, typed (Pydantic), async-first, automatically generates OpenAPI schema, well-suited for high-throughput API endpoints. |
| Redis | 7.2 | Message Broker & Cache | Used for task queueing (with Celery/RQ) and temporary execution states. |
| Celery | 5.4.0 | Asynchronous Worker Queue | Handles execution of the non-blocking `InvestigationPipeline` stages. |
| NetworkX | 3.3 | In-Memory Graph Engine | Python library for graph modeling of infrastructure and services; perfect for local in-memory root cause graph analysis. |
| Pydantic | 2.7.0 | Data Validation and Serialization | Enforces strict schema validations for `IncidentReportV1`, snapshots, and configuration models. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0.30 | Database ORM | Interface with PostgreSQL/SQLite for keeping track of investigations and audit logs. |
| google-genai | 0.1.1 | Google Gemini SDK | Connecting to Gemini models through `LLMProvider`. |
| anthropic | 0.28.0 | Anthropic Claude SDK | Connecting to Anthropic models through `LLMProvider`. |
| openai | 1.30.0 | OpenAI / OpenRouter SDK | Connecting to OpenAI and OpenRouter endpoints through `LLMProvider`. |
| httpx | 0.27.0 | Async HTTP Client | Performing API queries against Prometheus, Loki, GitHub, and Kubernetes APIs. |
| kubernetes | 30.1.0 | Kubernetes Client | Querying K8s state and events for evidence. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Docker | Containerization | Builds unified local run environment for API, workers, Redis, and integrations. |
| pytest | Test Harness | Handles unit testing, integration tests, and benchmarks suite. |
| Ruff | Linter & Formatter | Enforces clean Python style and speed. |
| Poetry / pip-tools | Dependency Management | Safe, deterministic lockfiles. |

## Installation

```bash
# Core Dependencies
pip install fastapi[all] celery redis networkx pydantic sqlalchemy psycopg2-binary httpx

# LLM Providers
pip install google-genai anthropic openai

# Integration Clients
pip install kubernetes

# Dev Dependencies
pip install pytest pytest-asyncio pytest-cov ruff black
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| NetworkX | Neo4j | When graph size exceeds RAM or when persistent visual graph querying is required. GraphProvider abstraction allows this swap. |
| Celery | RQ (Redis Queue) | If Celery configuration overhead is too high. Celery is chosen here for robust multi-worker features and broker support. |
| FastAPI | Django Ninja | If django admin is required out of the box. FastAPI is chosen for raw performance and simpler architecture. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| LangChain / LlamaIndex | Too much abstraction magic, difficult to debug, hard to customize for strict evidence logic. | Custom lightweight `LLMProvider` abstraction. |
| Direct HTTP calls to LLMs | Violates decoupling rules, makes mocking tests difficult. | Unified `LLMProvider` interface. |
| Synchronous Worker Execution | Blocking long-running investigation steps in API threads degrades throughput. | Celery / RQ background worker task queue. |

## Stack Patterns by Variant

**If Local / Open Source CLI mode:**
- Use SQLite for databases to avoid database infra overhead.
- Because it is lightweight and self-contained.

**If Production / Cloud Deploy:**
- Use PostgreSQL and Neo4j.
- Because persistent storage, concurrency, and scalable graph querying are needed.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Pydantic v2 | FastAPI v0.110+ | Requires updating Pydantic models to V2 definitions. |
| Celery v5 | Redis v7 | Standard broker integration. |

## Sources

- FastAPI Official Documentation — Async patterns.
- Celery Task Queue Documentation — Asynchronous runner patterns.
- NetworkX Network Analysis in Python — Benchmarks and usage limits.

---
*Stack research for: OpenSRE*
*Researched: 2026-06-07*
