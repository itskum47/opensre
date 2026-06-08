# Research: Common Pitfalls & Prevention

This document highlights critical pitfalls, warning signs, and prevention strategies to monitor during the execution of milestone v1.1.

## Pitfall Matrix

### 1. Hard Coupling to Neo4j
* **Description**: Writing code in the pipeline that assumes Neo4j is always available, causing investigations to crash if Neo4j is offline.
* **Warning Signs**: Pipeline exceptions during graph persistence blocking incident reporting.
* **Prevention Strategy**: Treat Neo4j as a secondary storage. The pipeline should log warnings and fallback to the in-memory NetworkX model if Neo4j connection fails.
* **Owner Phase**: Phase 1 (Neo4j Storage Layer).

### 2. Slack Block Kit Webhook Authentication Security Risk
* **Description**: Accepting Slack interactive blocks webhook calls without validating the Slack signature, allowing malicious actors to spoof approvals.
* **Warning Signs**: Unauthenticated requests to `/api/v1/slack/actions` executing remediation actions.
* **Prevention Strategy**: Implement standard Slack request signature verification middleware using the signing secret.
* **Owner Phase**: Phase 2 (Notification System).

### 3. Infinite Remediation Loop
* **Description**: Remediation script runs, alert triggers again, runs same script, creates infinite execution cycle.
* **Warning Signs**: Same remediation script executing repeatedly in a short time window.
* **Prevention Strategy**: Enforce a cooldown window (e.g., 1 hour) for executing remediation scripts on the same resource/service.
* **Owner Phase**: Phase 4 (Human-in-the-Loop Remediation).

### 4. Memory Similarity Drift
* **Description**: Over time, historical incident summaries drift, causing the memory engine to return false positive matches that distort RCA ranking.
* **Warning Signs**: Inaccurate historical recommendations in incident reports.
* **Prevention Strategy**: Only store incident reports where the root cause has been verified (manually or with high confidence). Add a `is_verified` flag to database and filter.
* **Owner Phase**: Phase 3 (Historical Incident Memory).

### 5. Frontend Visual Layout Bloat
* **Description**: Complex graph visualizations freezing the browser when an incident storm contains thousands of nodes.
* **Warning Signs**: Page lag and high CPU usage when viewing topology.
* **Prevention Strategy**: Limit visual nodes to the immediate blast radius (e.g., max 3 hops from the incident epicenter) and implement pagination or search filter in the graph view.
* **Owner Phase**: Phase 5 (Web Dashboard UI).
