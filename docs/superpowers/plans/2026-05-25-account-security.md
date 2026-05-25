# Account Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real password change and admin password reset workflows for trial operation.

**Architecture:** Extend existing FastAPI auth/users routers and services. Keep password hashing in `app.core.security`; expose small Vue dialogs/forms through existing admin and teacher settings pages.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest, Vue 3, Element Plus.

---

## File Structure

- Create `backend/tests/test_account_security.py`.
- Modify `backend/app/schemas/auth.py`.
- Modify `backend/app/schemas/user.py`.
- Modify `backend/app/services/auth_service.py`.
- Modify `backend/app/services/user_service.py`.
- Modify `backend/app/api/routers/auth.py`.
- Modify `backend/app/api/routers/users.py`.
- Modify `frontend/src/api/admin.ts`.
- Create `frontend/src/api/auth.ts` if no shared auth API file exists.
- Modify `frontend/src/views/admin/UserManagement.vue`.
- Modify `frontend/src/views/teacher/TeacherSettings.vue`.
- Update `docs/superpowers/progress/2026-05-25-platform-progress.md`.

## Tasks

### Task 1: Backend Red Tests

- [x] Write tests proving self password change, wrong-current-password blocking, admin reset, and non-admin reset blocking.
- [x] Run `python -m pytest backend/tests/test_account_security.py -q` and confirm red failures are missing endpoints.

### Task 2: Backend Implementation

- [x] Add `ChangePasswordRequest` and `ResetPasswordRequest`.
- [x] Add `AuthService.change_password`.
- [x] Add `UserService.reset_password`.
- [x] Add auth and user router endpoints with audit logs.
- [x] Run `python -m pytest backend/tests/test_account_security.py -q`.

### Task 3: Frontend Implementation

- [x] Add `changePassword` and `resetAdminUserPassword` API calls.
- [x] Add teacher settings password form with current/new/confirm fields.
- [x] Add admin reset password dialog in user management.
- [x] Run `npm run build`.

### Task 4: Verification and Push

- [ ] Run `python -m pytest backend/tests -q`.
- [ ] Run `python -m compileall backend\app`.
- [ ] Run `npm run build`.
- [ ] Run `git diff --check`.
- [ ] Commit and push `codex/agent-contract-crud`.
