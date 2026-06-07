---
phase: "03"
name: "timeline-correlation-sprint-3"
created: 2026-06-07
---

# Phase 3: Timeline & Correlation — Context

## Decisions

### 1. Unified Event Schema
- Every raw event from Loki, Prometheus, Kubernetes, and GitHub must normalize to a unified model:
  - `timestamp`: ISO-8601 UTC datetime.
  - `source_type`: 'prometheus', 'loki', 'kubernetes', or 'github'.
  - `source_id`: The ID or query name of the resource source.
  - `event_type`: Category of event (e.g., `metric_datapoint`, `log_entry`, `k8s_warning`, `git_commit`).
  - `description`: Textual summary (e.g., log message, metric value, commit subject).
  - `metadata`: Arbitrary payload dictionary for source-specific key-values (e.g. Pod name, namespace, author, commit hash).

### 2. Correlation Strategy
- We will group events using a **5-minute sliding window** and match them based on:
  - **Shared Labels**: Pod name (e.g. `auth-service`), namespace (`default`), container name (`redis`).
  - **Temporal Coincidence**: Correlate deployment events (GitHub commits) with subsequent log errors or CPU metric spikes occurring within the window.

## Discretion Areas

- The internal object models and auxiliary helper functions for timeline compilation.
- The exact layout of the persisted timeline output (e.g. JSON file `/app/events/{investigation_id}/timeline.json`).

## Deferred Ideas

- Advanced multi-dimensional metric correlation and cross-cluster trace aggregation (deferred to future milestones).
