# Organization Data Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JSON package import/export/template support for organization base data.

**Architecture:** Extend existing org router/service with non-destructive data portability endpoints. Keep import logic code-based and additive so it is safe for trial setup.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest, Vue 3, Element Plus.

---

## File Structure

- Create `backend/tests/test_org_data_portability.py`.
- Modify `backend/app/schemas/org.py`.
- Modify `backend/app/services/org_service.py`.
- Modify `backend/app/api/routers/org.py`.
- Modify `frontend/src/api/admin.ts`.
- Modify `frontend/src/views/admin/SchoolManagement.vue`.
- Update `docs/superpowers/progress/2026-05-25-platform-progress.md`.

## Tasks

### Task 1: Backend Red Tests

- [x] Write tests for template, export, dry-run import, committed import, repeated import skip, and role blocking.
- [x] Run `python -m pytest backend/tests/test_org_data_portability.py -q` and confirm red failures are missing endpoints.

### Task 2: Backend Import/Export

- [x] Add Pydantic schemas for organization data packages.
- [x] Add `OrgService.template_data_package`, `export_data_package`, and `import_data_package`.
- [x] Add `/org/data/template`, `/org/data/export`, and `/org/data/import` endpoints.
- [x] Run `python -m pytest backend/tests/test_org_data_portability.py -q`.

### Task 3: Frontend Import/Export Controls

- [x] Add admin API helpers for template/export/import.
- [x] Add controls on school management for template download, export download, dry-run import, and commit import.
- [x] Run `npm run build`.

### Task 4: Verification and Push

- [x] Update progress tracker.
- [x] Run `python -m pytest backend/tests -q`.
- [x] Run `python -m compileall backend\app`.
- [x] Run `npm run build`.
- [x] Run `git diff --check`.
- [x] Commit and push `codex/agent-contract-crud`.
