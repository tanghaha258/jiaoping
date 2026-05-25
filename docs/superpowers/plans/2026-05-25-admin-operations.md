# Admin Operations Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace admin placeholders with deployable CRUD and ledger pages for users, organization data, settings, audit logs, and AI call history.

**Architecture:** Add focused backend routers/services for organization data and system settings, reuse the current users/audit/AI call APIs, and build layered Vue admin pages with list/detail/dialog patterns. Keep role checks conservative and prefer soft delete or explicit inactive state over physical deletion.

**Tech Stack:** FastAPI, SQLAlchemy async, SQLite/PostgreSQL-compatible models, Vue 3, Element Plus, Vite, pytest.

---

### Task 1: Backend Organization and Settings APIs

**Files:**
- Create: `backend/app/schemas/org.py`
- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/services/org_service.py`
- Create: `backend/app/services/settings_service.py`
- Create: `backend/app/api/routers/org.py`
- Create: `backend/app/api/routers/settings.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_admin_operations.py`

- [x] Step 1: Add failing tests for organization CRUD, settings upsert, user management, and role blocking.
- [x] Step 2: Run the new backend tests and confirm the new endpoints fail before implementation.
- [x] Step 3: Implement organization schemas, service methods, and router endpoints.
- [x] Step 4: Implement settings schemas, service methods, and router endpoints.
- [x] Step 5: Include the new routers in the API v1 router.
- [x] Step 6: Run the new tests and all backend tests.

### Task 2: Admin Frontend API Layer

**Files:**
- Create: `frontend/src/api/admin.ts`
- Modify: `frontend/src/api/index.ts`

- [x] Step 1: Add typed helpers for users, org data, settings, audit logs, and AI calls.
- [x] Step 2: Export the new admin API module.
- [x] Step 3: Run frontend type/build verification after pages are connected.

### Task 3: Admin User and School Management Pages

**Files:**
- Modify: `frontend/src/views/admin/UserManagement.vue`
- Modify: `frontend/src/views/admin/SchoolManagement.vue`

- [x] Step 1: Replace user placeholder with real filters, table, detail drawer, create/edit dialog, and status action.
- [x] Step 2: Replace school placeholder with tabs for schools, classes, subjects, and regions.
- [x] Step 3: Wire all mutations to real APIs and reload affected lists.
- [x] Step 4: Run frontend build.

### Task 4: Admin Settings and Ledgers

**Files:**
- Modify: `frontend/src/views/admin/SystemSettings.vue`
- Modify: `frontend/src/views/admin/AuditLogViewer.vue`
- Modify: `frontend/src/views/admin/AICallHistory.vue`
- Modify: `frontend/src/views/admin/AdminDashboard.vue`

- [x] Step 1: Replace settings placeholder with JSON setting list and edit dialog.
- [x] Step 2: Replace audit log placeholder with filterable read-only ledger and detail drawer.
- [x] Step 3: Replace AI call placeholder with filterable read-only ledger, detail drawer, and progress block.
- [x] Step 4: Clean admin dashboard Chinese copy so it renders normally.
- [x] Step 5: Run frontend build.

### Task 5: Verification, Browser Smoke, Commit, Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`

- [x] Step 1: Run `python -m pytest backend/tests -q`.
- [x] Step 2: Run `python -m compileall backend\app`.
- [x] Step 3: Run `npm run build`.
- [x] Step 4: Browser smoke admin pages through Edge/Playwright.
- [x] Step 5: Update progress document.
- [x] Step 6: Commit and push branch `codex/agent-contract-crud`.
