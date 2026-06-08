# Research: Feature Capabilities

This document explores the typical behavior, table stakes, differentiators, and potential anti-features for the milestone v1.1 scope.

## Feature Mapping

### 1. Slack Notifications (`NOTF-01`)
* **Table Stakes**:
  * Send channel alerts when an investigation starts and finishes.
  * Render summary of findings, confidence score, and root cause hypothesis.
* **Differentiators**:
  * Interactive Slack Block Kit messages allowing users to trigger a manual runbook or approve a remediation action directly from Slack.
  * Slack thread updates for each pipeline stage transition (collect → correlate → timeline → graph → hypothesis → ranking).
* **Anti-Features**:
  * Chatbot conversations (complex natural language processing is out of scope; notifications should be action-oriented).

### 2. PagerDuty Integration (`NOTF-02`)
* **Table Stakes**:
  * Match incoming PagerDuty alerts with new OpenSRE investigations.
  * Acknowledge/resolve PagerDuty incidents automatically when OpenSRE starts/concludes investigations.
* **Differentiators**:
  * Bidirectional sync: user acknowledging on PagerDuty triggers a snapshot reload/status update in OpenSRE.
  * Append OpenSRE timeline link and root cause summary as notes to the PagerDuty incident.
* **Anti-Features**:
  * Creating a custom incident management scheduler (PagerDuty remains the scheduler of record).

### 3. Neo4j Graph Storage (`NEO4-01`)
* **Table Stakes**:
  * Persist the NetworkX service topology and incident dependency graphs into Neo4j database.
  * Run path tracing algorithms to find common dependencies during incident storms.
* **Differentiators**:
  * Real-time query capability to explore nodes (services, databases, pods) and edges (dependencies, network calls) across multiple concurrent investigations.
  * Visualizing service blast radius using PageRank or centralities in Neo4j.
* **Anti-Features**:
  * Replacing SQLite as the main app database (SQLite holds state/metadata; Neo4j is purely for graph topology analysis).

### 4. Historical Memory RCA (`MEM-01`)
* **Table Stakes**:
  * Vectorize incident snapshots (logs, metrics, alerts, root causes).
  * Run similarity queries when a new incident occurs to find matching historical incidents.
* **Differentiators**:
  * Weight similarity scores based on evidence overlap (e.g., matching database logs and error messages).
  * Automatically suggest remediation plans that succeeded in past similar incidents.
* **Anti-Features**:
  * Generative incident synthesis (relying on raw LLM guesses instead of retrieving actual historical evidence).

### 5. Human-in-the-Loop Remediation (`REMED-01`)
* **Table Stakes**:
  * Propose remediation scripts/actions based on the ranked hypothesis.
  * Require manual user confirmation before executing any command.
* **Differentiators**:
  * One-click execution from Slack or UI dashboard.
  * Automated post-remediation validation (running checks to verify if the incident alert cleared).
* **Anti-Features**:
  * Fully autonomous self-healing without gates (too risky for production environments).

### 6. Dashboard UI (`UI-01`)
* **Table Stakes**:
  * List past and current investigations with status and timestamps.
  * Interactive chronological timeline view.
* **Differentiators**:
  * Interactive D3-based dependency graph showing service topology and highlighting the suspected root cause.
  * Real-time update streams via WebSockets for active pipeline execution.
* **Anti-Features**:
  * Code editors or configuration panels (UI should focus on visual investigation analysis, not app editing).
