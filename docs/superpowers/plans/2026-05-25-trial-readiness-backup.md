# Trial Readiness and Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an admin-visible trial readiness checklist and repeatable SQLite backup/restore scripts for local school pilots.

**Architecture:** Extend the existing dashboard API with one admin-only aggregate endpoint. Keep checks read-only and computed from current database state, then surface the same contract in the admin dashboard as an operational checklist.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, pytest, Vue 3, Element Plus, PowerShell.

---

## File Structure

- Create `backend/tests/test_trial_readiness.py` for API contract, role blocking, and operational artifact tests.
- Modify `backend/app/api/routers/dashboard.py` to expose `/dashboard/trial-readiness`.
- Modify `backend/app/services/dashboard_service.py` to compute checklist items.
- Modify `frontend/src/api/dashboard.ts` to add TypeScript types and API helper.
- Modify `frontend/src/views/admin/AdminDashboard.vue` to show the checklist and clean Chinese copy.
- Create `scripts/backup-sqlite.ps1` for timestamped SQLite backups.
- Create `scripts/restore-sqlite.ps1` for guarded SQLite restores.
- Modify `docs/DEPLOYMENT.md` with backup and restore commands.
- Update `docs/superpowers/progress/2026-05-25-platform-progress.md`.

## Tasks

### Task 1: Backend Red Tests

- [x] Create `backend/tests/test_trial_readiness.py`.
- [x] Add helper `_login(client, username)` using `admin/admin123` and `teacher001/password`.
- [x] Add `test_system_admin_can_view_trial_readiness_checklist` asserting:
  - `GET /api/v1/dashboard/trial-readiness` returns 200 for admin.
  - `data.status` is `ready` or `action_required`.
  - `summary` has `ok`, `warning`, and `error`.
  - `items` contains `service_readiness`, `organization_data`, `user_accounts`, `ai_contract`, `teaching_workflow`, `student_task_availability`, `resources`, and `backup_path`.
  - Each item has `key`, `label`, `status`, `description`, `metric`, `action`, and `route`.
- [x] Add `test_non_admin_cannot_view_trial_readiness_checklist` expecting 403 for `teacher001`.
- [x] Add `test_backup_restore_artifacts_are_documented` asserting:
  - `scripts/backup-sqlite.ps1` exists and contains `Copy-Item`.
  - `scripts/restore-sqlite.ps1` exists and contains `SkipSafetyBackup` plus a pre-restore backup copy.
  - `docs/DEPLOYMENT.md` contains `SQLite Backup` and `SQLite Restore`.
- [x] Run `python -m pytest backend/tests/test_trial_readiness.py -q`.
- [x] Confirm the red failure is caused by the missing endpoint and missing scripts/docs.

### Task 2: Backend Trial Readiness API

- [x] Import `require_roles` in `backend/app/api/routers/dashboard.py`.
- [x] Add admin-role `GET /dashboard/trial-readiness`.
- [x] Add `DashboardService.get_trial_readiness(db)` returning:
  - `status`: `ready` when no item is `error`, otherwise `action_required`.
  - `checked_at`: current UTC ISO timestamp.
  - `summary`: counts for `ok`, `warning`, and `error`.
  - `items`: the eight planned checklist items.
- [x] Count schools/classes/subjects/users/AI agents/projects/tasks/resources with SQLAlchemy `select(func.count())`.
- [x] Treat organization data, teacher/student accounts, and enabled lesson-plan AI agents as blocking `error` when missing.
- [x] Treat missing workflow data, published tasks, and resources as `warning`.
- [x] Run `python -m pytest backend/tests/test_trial_readiness.py -q` and confirm endpoint tests pass while script artifacts remain red.

### Task 3: Backup and Restore Scripts

- [x] Create `scripts/backup-sqlite.ps1` with parameters `DatabasePath` and `BackupDir`.
- [x] Resolve a default database path from `backend/.env` when possible, falling back to `backend/app.db`.
- [x] Validate the database file exists, create the backup directory, and `Copy-Item -LiteralPath $resolvedDatabase -Destination $target`.
- [x] Create `scripts/restore-sqlite.ps1` with parameters `BackupPath`, `DatabasePath`, and `SkipSafetyBackup`.
- [x] Validate the backup file exists.
- [x] When target database exists and `SkipSafetyBackup` is false, copy the current database to `*.pre-restore-YYYYMMDD-HHMMSS.db`.
- [x] Copy the backup to the target with `Copy-Item -LiteralPath $resolvedBackup -Destination $resolvedDatabase -Force`.
- [x] Update `docs/DEPLOYMENT.md` with `SQLite Backup` and `SQLite Restore` sections.
- [x] Run `python -m pytest backend/tests/test_trial_readiness.py -q`.

### Task 4: Frontend Dashboard Panel

- [x] Add `TrialReadiness`, `TrialReadinessItem`, and related status types in `frontend/src/api/dashboard.ts`.
- [x] Add `getTrialReadiness()` calling `/dashboard/trial-readiness`.
- [x] Rewrite `frontend/src/views/admin/AdminDashboard.vue` into clean Chinese copy while keeping existing overview, project trends, and AI usage cards.
- [x] Load readiness data with the dashboard requests.
- [x] Show a "试运行检查清单" panel with summary counters, status tags, item metric/action/description, and quick route buttons.
- [x] Run `npm run build`.

### Task 5: Verification, Smoke, Commit, Push

- [x] Update `docs/superpowers/progress/2026-05-25-platform-progress.md` with Phase 8 progress.
- [x] Run `python -m pytest backend/tests/test_trial_readiness.py -q`.
- [x] Run `powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1`.
- [x] Run `git diff --check`.
- [x] Smoke test `/admin` in a browser and confirm "试运行检查清单" renders.
- [ ] Commit with `git commit -m "Add trial readiness checklist and backups"`.
- [ ] Push `codex/agent-contract-crud` and confirm the remote accepts Phase 7 plus Phase 8.
