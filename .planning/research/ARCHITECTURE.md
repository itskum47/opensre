# Architecture Research

**Domain:** AI-driven SRE & Incident Investigation Platform
**Researched:** 2026-06-07
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                           │
│     (FastAPI Endpoints, CLI commands, Slack/PagerDuty Webhooks)│
├─────────────────────────────────────────────────────────────┤
│                    Application Services                     │
│    (Orchestrators, InvestigationPipeline runner, Worker Jobs)│
├─────────────────────────────────────────────────────────────┤
│                        Domain Layer                         │
│  (incidents, evidence, timeline, graph, ranking, audit, memory)│
├─────────────────────────────────────────────────────────────┤
│                   Providers / Integrations                  │
│  (LLMProvider, GraphProvider, Prometheus, Loki, K8s, GitHub)│
├─────────────────────────────────────────────────────────────┤
│                           Storage                           │
│        (Event Store, SQLite/PostgreSQL, File Snapshots)     │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| API Layer | Receives requests, triggers async investigations, returns job IDs, serves snapshots. | FastAPI async router endpoints. |
| Application Services | Coordinates the `InvestigationPipeline` stages, handles background task dispatch. | Celery/RQ task runner. |
| Domain Layer | Pure business logic for evidence normalization, timeline sorting, graph modeling, ranking, audit records. | Pure Python classes. |
| Providers Layer | Interfaces with external APIs, databases, or LLMs. Shields domain from vendor details. | Implementations of `LLMProvider`, `GraphProvider`. |
| Storage Layer | Reads and writes raw event payloads, investigation snapshots, audits, and metadata. | File-based Event Store and SQL database (SQLAlchemy). |

## Recommended Project Structure

```
opensre/
├── backend/
│   ├── app/
│   │   ├── api/             # API Router endpoints
│   │   ├── services/        # Application orchestrators
│   │   ├── domain/          # Core business logic
│   │   │   ├── incidents/
│   │   │   ├── evidence/
│   │   │   ├── timeline/
│   │   │   ├── graph/
│   │   │   ├── ranking/
│   │   │   ├── memory/
│   │   │   ├── remediation/
│   │   │   ├── ownership/
│   │   │   └── audit/
│   │   ├── providers/       # LLM, Graph, and Integrations
│   │   ├── events/          # Immutable Event Store
│   │   ├── workers/         # Background worker setup
│   │   └── config/          # Configurations & Feature Flags
│   └── tests/               # Backend tests
├── cli/                     # CLI codebase
├── sdk/                     # Plugin SDK (DataSource, Agent, Graph, Remediation)
├── integrations/            # Connectors (Prometheus, Loki, GitHub, etc.)
├── infra/                   # Docker, docker-compose, and deploy configs
└── tests/
    └── benchmarks/          # Scenario evaluation tests
```

### Structure Rationale

- **backend/app/domain/:** Business logic is strictly separated from presentation and infrastructure. This enables testability and code reuse between the FastAPI API, CLI, and agents.
- **backend/app/providers/:** Standardizes external integrations (LLMProvider, GraphProvider) to allow swapping implementations (e.g. OpenAI vs Gemini, NetworkX vs Neo4j) without modifying domain logic.
- **backend/app/events/:** Immutable storage of raw events. Never mutates raw evidence, satisfying Rule 5.

## Architectural Patterns

### Pattern 1: Multi-LLM Router (`LLMProvider`)

**What:** Standardized provider interface for invoking different models (OpenAI, Anthropic, Gemini, Ollama, OpenRouter).
**When to use:** All LLM operations.
**Trade-offs:** Custom routing requires mapping standardized model parameters (temperature, prompts) across multiple SDK structures, but prevents hardcoding.

**Example:**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, schema: Type[BaseModel], **kwargs) -> BaseModel:
        pass

class GeminiProvider(LLMProvider):
    async def generate(self, prompt: str, schema: Type[BaseModel], **kwargs) -> BaseModel:
        # Calls google-genai structured output
        pass
```

### Pattern 2: Investigation Pipeline State Machine

**What:** Class that tracks investigation state as it transitions from collection to reporting.
**When to use:** Throughout an active investigation.
**Trade-offs:** Sequential stage execution can be slow, but ensures reproducibility and deterministic timelines.

## Data Flow

### Request Flow

```
[POST /investigations]
        ↓
[FastAPI Router] ── (enqueue) ──> [Redis Task Queue]
        ↓                                 │
[Return Job ID]                           │ (worker picks up)
                                          ▼
                               [Worker Executor]
                                          │
                               [InvestigationPipeline]
                                          │ 
                      ┌───────────────────┴───────────────────┐
                      ▼                                       ▼
             [Collect & Normalize]                    [Graph & Rank RCA]
                      │                                       │
            (Write Event Store)                              (RCA)
                      │                                       │
                      └───────────────────┬───────────────────┘
                                          ▼
                                [Generate Snapshots]
                                          │
                                  (Write SQL DB)
```

### Key Data Flows

1. **Investigation Pipeline Loop:** The worker loops through: `collect` -> `normalize` -> `correlate` -> `timeline` -> `graph` -> `hypothesize` -> `rank` -> `report`. It fetches credentials/configs, stores events, invokes LLMs/rankers, writes snapshot files, and completes the run.
2. **Audit Logging:** Any stage entry/exit or action registers an immutable record in `AuditTrail`, which is saved to SQLite/PostgreSQL.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 runs/day | Single monolith instance with SQLite database, NetworkX in-memory graphs, and single Celery worker. |
| 100-10k runs/day | Multi-container deploy: FastAPI replication, PostgreSQL database, dedicated Neo4j instance, multiple Celery workers on Redis cluster. |

## Sources

- Clean Architecture principles (Robert C. Martin).
- Standard monorepo structures.

---
*Architecture research for: OpenSRE*
*Researched: 2026-06-07*
