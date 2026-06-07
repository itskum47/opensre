# Phase 2: Integrations (Sprint 2) - Context

**Gathered:** 2026-06-07T10:55:00+05:30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase implements integration plugins (Data Sources) for Kubernetes, Prometheus, Loki, and GitHub. These plugins gather cluster events, metrics, logs, and commit histories respectively, normalizes the output payloads, and writes them directly to the write-once Event Store in preparation for correlation and timeline compilation.

</domain>

<decisions>
## Implementation Decisions

### Kubernetes Integration
- **Credentials Loading Strategy**: Attempt in-cluster config loading first, falling back to local `~/.kube/config` loading.
- **Resource State Scope**: Query and track Pods, Services, Events, and Deployments for SRE analysis.

### Prometheus & Loki Integrations
- **Prometheus Queries**: Query Prometheus via its HTTP REST API using `httpx` async client to keep dependencies clean.
- **Loki Queries**: Set limits to fetch a maximum of 1000 log lines per query with exact start/end timestamp ranges to avoid memory leaks.

### GitHub Integration
- **Commit History Retrieval**: Retrieve commits matching the investigation time range, capped at the last 100 commits or last 7 days.
- **Authentication**: Authenticate using a Personal Access Token (PAT) configured via environment variables.

### Claude's Discretion
- Code structural patterns, routing classes, and client connection setups are left to Claude's discretion.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/events/store.py` (`EventStore`): Writes events to `/app/events/{investigation_id}/`.
- `backend/app/config/settings.py` (`Settings`): Reads environment variables.

### Established Patterns
- Pydantic models for structured configurations.
- SQLAlchemy listeners for database audits.

### Integration Points
- Normalizer pipelines: DataSources must output normalized dictionaries suitable for the `EventStore`.

</code_context>

<specifics>
## Specific Ideas

- Implement a mock mode for each integration (K8s, Prometheus, Loki, GitHub) to allow local test suites to execute without live endpoints.

</specifics>

<deferred>
## Deferred Ideas

- Tempo, Grafana, Slack, and PagerDuty integrations (deferred to Phase 4 / v2).
- Terraform, AWS, Azure, GCP, GitLab, OpsGenie (deferred to v2 / Tier 3).

</deferred>
