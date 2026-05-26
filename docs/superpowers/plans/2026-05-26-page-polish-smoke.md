# Page Polish And Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reliable Phase 9 baseline that detects broken frontend text, protects key route/navigation labels, and runs during release checks.

**Architecture:** Use a fast static Python checker under `scripts/` so page-text regressions are caught without starting services. Keep route/navigation expectations in the checker and cover the checker itself with pytest artifact tests.

**Tech Stack:** Python 3, pytest, Vue 3, Vue Router, PowerShell release script.

---

### Task 1: Frontend Text Health Red Test

**Files:**
- Create: `backend/tests/test_frontend_text_health.py`
- Later create: `scripts/check_frontend_text_health.py`
- Later modify: `scripts/check-release.ps1`

- [x] **Step 1: Write the failing test**

Create `backend/tests/test_frontend_text_health.py` with tests that assert the script exists, passes, checks expected labels, and is wired into release checks.

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest backend/tests/test_frontend_text_health.py -q`

Expected: FAIL because `scripts/check_frontend_text_health.py` does not exist yet.

### Task 2: Implement Text Health Check

**Files:**
- Create: `scripts/check_frontend_text_health.py`
- Modify: `scripts/check-release.ps1`

- [x] **Step 1: Create the checker**

Implement a Python script that reads frontend source files as UTF-8, rejects replacement characters/common mojibake tokens/broken template fragments, and verifies expected route/navigation labels.

- [x] **Step 2: Add it to release checks**

Call `python scripts\check_frontend_text_health.py` from `scripts/check-release.ps1` before the frontend build.

- [x] **Step 3: Run test to verify it passes**

Run: `python -m pytest backend/tests/test_frontend_text_health.py -q`

Expected: PASS.

### Task 3: Phase Progress Update

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`

- [x] **Step 1: Add Phase 9/10 progress entries**

Record Phase 9 as active and Phase 10 as the upcoming AI contract foundation track.

- [x] **Step 2: Mark completed Phase 9 baseline work**

After tests pass, mark the text-health checker and release integration as complete.

### Task 4: Verification And Git

**Files:**
- All changed files

- [x] **Step 1: Run targeted test**

Run: `python -m pytest backend/tests/test_frontend_text_health.py -q`

Expected: PASS.

- [x] **Step 2: Run release checks**

Run: `powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1`

Expected: backend tests pass, backend compile passes, frontend text health passes, frontend build passes.

- [x] **Step 3: Inspect diff**

Run: `git diff --check`, `git status --short`, and `git diff --stat`.

- [ ] **Step 4: Commit and push**

Commit message: `Add frontend text health checks`

Push branch: `codex/agent-contract-crud`.
