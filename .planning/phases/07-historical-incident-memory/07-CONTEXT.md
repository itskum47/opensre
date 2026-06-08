# Phase 7: Historical Incident Memory - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase implements a local, deterministic incident memory engine in SQLite that indexes historical incident profiles and matches them against active investigations using Jaccard similarity. Similar profiles feed into the RootCauseRanker and suggest remediation actions.

</domain>

<decisions>
## Implementation Decisions

### Similarity Metric
- **Comparison**: Use Jaccard overlap similarity matching on resource keys, error log tokens, and active alerts.
- **Offline / Deterministic**: Keep it completely offline and deterministic to avoid external API key dependencies and ensure fast local tests.

### SQLite Storage Schema
- **Database Table**: Create a `historical_incidents` table in the main SQLite database.
- **Fields**: Store `id`, `investigation_id`, `keys` (JSON array), `alerts` (JSON array), `error_tokens` (JSON array), and `remediation_action` (JSON dict).

### Rank Integration
- **Threshold**: Only match incidents with similarity $> 0.2$ (20% overlap).
- **Score Influence**: Add up to 0.25 weight to the `RootCauseRanker` confidence score if there is a matching historical incident.

### Claude's Discretion
- Database ORM model mappings and Jaccard weights combination logic are left to Claude's discretion.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- Database session context in `backend/app/database.py`.
- `RootCauseRanker` in `backend/app/domain/incidents/ranker.py`.

### Integration Points
- `RootCauseRanker` calculates hypothesis scores during the `rank` pipeline stage. We will invoke memory queries here.

</code_context>

<specifics>
## Specific Ideas

- None — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Neo4j Graph Embeddings — deferred to future phases.

</deferred>
