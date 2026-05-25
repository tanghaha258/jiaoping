# User Account Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JSON template/export/import support for trial teacher and student account initialization.

**Architecture:** Extend the existing user router/service with additive data portability endpoints. Keep organization resolution by school code and class identity so packages remain portable between databases.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, pytest, Vue 3, Element Plus.

---

## File Structure

- Create `backend/tests/test_user_account_portability.py`.
- Modify `backend/app/schemas/user.py`.
- Modify `backend/app/services/user_service.py`.
- Modify `backend/app/api/routers/users.py`.
- Modify `frontend/src/api/admin.ts`.
- Modify `frontend/src/views/admin/UserManagement.vue`.
- Update `docs/superpowers/progress/2026-05-25-platform-progress.md`.

## Tasks

### Task 1: Backend Red Tests

- [x] Write tests for template, export redaction, dry-run import, committed import, login with imported password, repeated import skip, student class binding, and role blocking.
- [x] Run `python -m pytest backend/tests/test_user_account_portability.py -q` and confirm failures are missing endpoints.

### Task 2: Backend User Import/Export

- [x] Add Pydantic schemas for user data packages with API alias `class`.
- [x] Add `UserService.template_data_package`, `export_data_package`, and `import_data_package`.
- [x] Add `/users/data/template`, `/users/data/export`, and `/users/data/import` before parameterized user routes.
- [x] Add audit logging for committed imports.
- [x] Run `python -m pytest backend/tests/test_user_account_portability.py -q`.

### Task 3: Frontend User Import/Export Controls

- [x] Add admin API types and helpers for user account template/export/import.
- [x] Add controls to user management for template download, export download, dry-run import, and commit import.
- [x] Show import summary, errors, and temporary new-account password handout list.
- [x] Run `npm run build`.

### Task 4: Verification and Push

- [x] Update progress tracker.
- [x] Run `python -m pytest backend/tests -q`.
- [x] Run `python -m compileall backend\app`.
- [x] Run `npm run build`.
- [x] Run `git diff --check`.
- [x] Browser-smoke admin user management import/export controls.
- [ ] Commit and push `codex/agent-contract-crud`.
