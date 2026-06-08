# Phase 5: Neo4j Storage Layer - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase implements a persistent graph storage layer in Neo4j to store service topologies and incident graphs generated during pipeline runs, supporting graph queries to trace shared dependencies across concurrent investigations.

</domain>

<decisions>
## Implementation Decisions

### Neo4j Connection Management
- **Settings Config**: Add `NEO4J_URI` (default `bolt://localhost:7687`), `NEO4J_USER` (default `neo4j`), and `NEO4J_PASSWORD` (default `password`) to `backend/app/config/settings.py`.
- **Pool Lifecycle**: The Neo4j driver connection pool is initialized on FastAPI application startup and closed gracefully on shutdown.
- **Failure Fallback**: The pipeline must not crash if Neo4j is unreachable. Operations should catch connection exceptions, log warnings, and fallback to the standard in-memory NetworkX model.

### Graph Model Schema
- **Node/Edge Modeling**: Node labels are maps to service topology entities (`Service`, `Pod`, `Alert`, `Metric`) with relationship types (`DEPENDS_ON`, `CALLS`, `RUNS_ON`, `TRIGGERED_BY`).
- **Incident Separation**: Graph nodes and edges have an `investigation_id` property to isolate subgraphs and perform query boundaries per investigation.

### Graph Querying
- **Cypher Interface**: Queries are written in Cypher and executed using the official `neo4j` driver's session/transaction API.
- **Path Tracing**: Implements a shared dependency trace query returning common ancestor nodes within $N$ hops from active alert nodes.

### Claude's Discretion
- Neo4j session write transaction retries and driver pooling configurations are left to Claude's discretion.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GraphProvider` in `backend/app/domain/incidents/graph.py` currently handles NetworkX `DiGraph` operations and serves as the primary graph interface.

### Established Patterns
- Pydantic-based configuration settings in `backend/app/config/settings.py` for API/integration endpoints.
- Dependency injection or global state initialization via Lifespan in FastAPI.

### Integration Points
- `InvestigationPipeline` under `backend/app/domain/incidents/pipeline.py` initializes `GraphProvider` during the `graph` stage.

</code_context>

<specifics>
## Specific Ideas

- None — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Neo4j Graph Data Science (GDS) library usage — deferred for future optimization.

</deferred>
