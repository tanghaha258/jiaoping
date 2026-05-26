# Page Route Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Phase 9 static route smoke check that protects the core admin, teacher, student, and research page entry points before deeper visual polish.

**Architecture:** Add a Python script under `scripts/` that reads Vue Router config and selected page components as UTF-8. The script checks required route paths, route titles, component files, and page-level anchor labels, then runs during release checks.

**Tech Stack:** Python 3, pytest, Vue 3, Vue Router, PowerShell release script.

---

### Task 1: Route Smoke Red Test

**Files:**
- Create: `backend/tests/test_frontend_route_smoke.py`
- Later create: `scripts/check_frontend_route_smoke.py`
- Later modify: `scripts/check-release.ps1`

- [x] **Step 1: Write the failing test**

Create tests that assert the route smoke script exists, passes, reports the number of checked routes, and is wired into release checks.

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_frontend_route_smoke.py -q`

Expected: FAIL because `scripts/check_frontend_route_smoke.py` does not exist yet.

### Task 2: Implement Route Smoke Check

**Files:**
- Create: `scripts/check_frontend_route_smoke.py`
- Modify: `scripts/check-release.ps1`

- [x] **Step 1: Create the checker**

Implement a Python script that validates the core routes and page anchors listed in the Phase 9 design.

- [x] **Step 2: Add it to release checks**

Call `python scripts\check_frontend_route_smoke.py` from `scripts/check-release.ps1` after text health and before frontend build.

- [x] **Step 3: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_frontend_route_smoke.py -q`

Expected: PASS.

### Task 3: Verification And Progress

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-26-page-route-smoke.md`

- [x] **Step 1: Run targeted tests**

Run:

```powershell
python -m pytest backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
```

Expected: PASS.

- [x] **Step 2: Run release checks**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected: backend tests pass, backend compile passes, frontend text health passes, route smoke passes, frontend build passes.

- [x] **Step 3: Browser smoke**

Open `/admin/ai-agents` and `/teacher/ai/lesson-plan` in the in-app browser and verify title/key Chinese text is visible.

- [ ] **Step 4: Commit and push**

Commit message: `Add frontend route smoke checks`

Push branch: `codex/agent-contract-crud`.
