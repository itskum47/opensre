# Phase 8: Human-in-the-Loop Remediation - Context

**Date:** 2026-06-08
**Status:** Completed

## Phase Boundary
Implement stateful approval, cooldown checks, script execution, and post-execution validation checks for suggested remediations. Ensure that actions are queued or run asynchronously through Celery only after operator approval via Slack webhooks or REST API.

## Design Decisions
1. **Remediation States**: Held in `PENDING_APPROVAL` initially, transitioning to `APPROVED`/`REJECTED`, then `EXECUTING`, and finally `COMPLETED`/`FAILED`.
2. **Safety Cooldowns**: Standard 5-minute cooldown per action/target combination to block duplicate/cascading runs.
3. **Validation Health Checks**: Simulated health validation checking (e.g. check for unhealthy pods or high CPU rates) to automatically verify recovery post-execution.
