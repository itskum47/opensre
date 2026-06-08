# Phase 6: Slack & PagerDuty Notifications - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase implements notification clients for Slack and PagerDuty, routing pipeline state transitions (started, completed) to external channels, supporting bidirectional PagerDuty notes/status sync, and exposing a secure FastAPI webhook verification endpoint to receive Slack interactive block actions.

</domain>

<decisions>
## Implementation Decisions

### Slack Webhook & Signature Verification
- **Verification**: Enforce HMAC SHA256 signature verification matching `SLACK_SIGNING_SECRET` in FastAPI dependency middleware.
- **Actions**: Support `approve_remediation` and `reject_remediation` action callbacks.

### PagerDuty Sync Protocol
- **Mapping**: OpenSRE pipeline start triggers PagerDuty Acknowledge; pipeline completion triggers PagerDuty Resolve.
- **Notes**: Post OpenSRE timeline reports and root cause findings as formatted PagerDuty incident notes.

### Notification Router Hook
- **Trigger**: Expose a central `NotificationRouter` class invoked during Celery async pipeline stage transitions.
- **Error Tolerance**: If notification services are offline, catch exceptions, log warnings, and proceed without blocking the main pipeline.

### Claude's Discretion
- Formats of Slack blocks and PagerDuty notes messages are left to Claude's discretion.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Settings` in `backend/app/config/settings.py` (has `ENABLE_SLACK`, `ENABLE_PAGERDUTY`).

### Integration Points
- `InvestigationPipeline` in `backend/app/domain/incidents/pipeline.py` executes Celery tasks; we will invoke notifications here.

</code_context>

<specifics>
## Specific Ideas

- None — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Sending logs/traces attachment payload directly to Slack — deferred to future.

</deferred>
