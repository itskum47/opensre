---
phase: "04"
name: "graph-engine-root-cause-ranking-sprint-4"
created: 2026-06-07
---

# Phase 4: Graph Engine & Root Cause Ranking — Context

## Decisions

### 1. Service Topology Graph (NetworkX)
- Implement `GraphProvider` using the `networkx` library to build a directed graph (DiGraph) representing the system dependency map (e.g. `auth-service` -> `db-service`).
- Nodes represent services/pods. Edges represent dependencies or communication channels.
- Populate edges dynamically from Kubernetes service/deployment definitions, or use a static dependency map for the target namespaces.

### 2. Multi-Factor Hypothesis Ranking
- Implement `RootCauseRanker` evaluating root cause hypotheses. For each correlated group, calculate a confidence score between 0.0 and 1.0 using the formula:
  `Confidence = (w1 * Temporal + w2 * EvidenceDensity + w3 * SourceReliability + w4 * ChangeHistory)`
  - **Temporal**: Proximity of events to the investigation start time.
  - **EvidenceDensity**: Ratio of warning/error events to total events in the correlated group.
  - **SourceReliability**: Higher weight for Kubernetes probe failures and Loki logs containing "Error"/"Exception", lower for raw metric updates.
  - **ChangeHistory**: Highest weight if there is a matching Git commit (deployment) in the correlated group.

### 3. OpenSRE CLI
- Add command-line interface `opensre` with subcommands:
  - `investigate <investigation_id>`: Runs the full pipeline and prints a summary.
  - `explain <investigation_id>`: Queries the LLM provider to construct a detailed explanation narrative of the root cause using the ranked hypotheses.

### 4. Synthetic Incident Benchmarks
- Create benchmark tests simulating:
  - `redis_saturation`: Spike in Redis CPU/metrics followed by connection errors.
  - `database_outage`: K8s warning events + DB log errors + API errors.

## Discretion Areas

- The exact weights used in the multi-factor scoring formula (e.g. default equal weights `0.25` each).
- The exact prompt layout passed to the `LLMProvider` in `opensre explain` command.

## Deferred Ideas

- Persistent visual graph rendering in web dashboard (deferred to v2).
