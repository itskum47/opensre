---
phase: 1
slug: foundation-sprint-1
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-07
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `pytest -m unit` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -m unit`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | DOCK-01 | unit | `pytest backend/tests/test_config.py` | ✅ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | ROUT-01 | unit | `pytest backend/tests/test_llm.py -k test_mock_provider` | ✅ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | ROUT-02, ROUT-03 | unit | `pytest backend/tests/test_llm.py -k test_adapters` | ✅ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | STOR-01, STOR-02 | unit | `pytest backend/tests/test_events.py` | ✅ W0 | ⬜ pending |
| 1-02-02 | 02 | 2 | AUDT-01 | unit | `pytest backend/tests/test_audit.py` | ✅ W0 | ⬜ pending |
| 1-02-03 | 02 | 2 | PIPE-01, PIPE-02 | unit | `pytest backend/tests/test_pipeline.py` | ✅ W0 | ⬜ pending |
| 1-02-04 | 02 | 2 | WORK-01, WORK-02 | unit | `pytest backend/tests/test_workers.py` | ✅ W0 | ⬜ pending |
| 1-03-01 | 03 | 3 | SNAP-01, SNAP-02, REPT-01 | unit | `pytest backend/tests/test_snapshots.py` | ✅ W0 | ⬜ pending |
| 1-03-02 | 03 | 3 | DOCK-01 | unit | `docker-compose config` | ❌ W0 | ⬜ pending |
| 1-03-03 | 03 | 3 | DOCK-02 | unit | `pytest backend/tests/test_cicd.py` | ✅ W0 | ⬜ pending |
| 1-03-04 | 03 | 3 | DOCK-01 | integration | `pytest` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_llm.py` — Stubs for mock provider and adapter verifications
- [ ] `backend/tests/test_config.py` — Stubs for backend settings and feature flags
- [ ] `backend/tests/test_events.py` — Stubs for checking event store directory and file write validations
- [ ] `backend/tests/test_audit.py` — Stubs for mapping SQLAlchemy audit entry/immutability constraints
- [ ] `backend/tests/test_pipeline.py` — Stubs for checking Investigation pipeline status changes
- [ ] `backend/tests/test_workers.py` — Stubs for worker async tasks enqueuing
- [ ] `backend/tests/test_snapshots.py` — Stubs for validating IncidentReportV1 schema and snapshots
- [ ] `backend/tests/test_cicd.py` — Stubs for validating GitHub Actions/GitLab CI configurations format

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
