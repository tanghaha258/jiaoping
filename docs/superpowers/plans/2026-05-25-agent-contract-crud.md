# Agent Contract, Module Hierarchy, and Real CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the platform operational instead of demo-only by defining local AI-agent contracts, adding AI thinking progress tracking, and landing real CRUD for key modules.

**Architecture:** Keep external AI calls behind local workflow contracts. Business modules use real backend CRUD APIs and layered frontend views: list, detail drawer/dialog, create/edit dialog, and explicit state actions.

**Tech Stack:** FastAPI, SQLAlchemy async, SQLite/PostgreSQL-compatible models, Vue 3, Element Plus, Vite.

---

### Task 1: AI Agent Contract and Thinking Progress

**Files:**
- Create: `backend/app/models/ai_call_step.py`
- Modify: `backend/app/core/ai_schemas.py`
- Modify: `backend/app/services/ai_service.py`
- Modify: `backend/app/services/lesson_plan_workflow.py`
- Modify: `backend/app/api/routers/ai.py`
- Test: `backend/tests/test_ai_contract_progress.py`

- [x] Step 1: Add tests for `/ai/contracts` and `/ai/calls/{id}/progress`.
- [x] Step 2: Run tests and confirm they fail because the endpoints do not exist.
- [x] Step 3: Add `AICallStep` model and progress serialization.
- [x] Step 4: Return local contract definitions for each AI scenario.
- [x] Step 5: Insert/update thinking steps when lesson-plan drafts are generated and adopted.
- [x] Step 6: Run tests and compile backend.

### Task 2: Admin AI Agent CRUD

**Files:**
- Modify: `backend/app/services/ai_service.py`
- Modify: `backend/app/api/routers/ai.py`
- Test: `backend/tests/test_ai_agent_crud.py`
- Modify: `frontend/src/api/ai.ts`
- Modify: `frontend/src/views/admin/AIAgentConfig.vue`

- [x] Step 1: Add typed create/update agent API helpers.
- [x] Step 2: Add backend soft-delete support so CRUD is complete.
- [x] Step 3: Replace placeholder admin page with list, filters, detail drawer, create/edit dialog, and enable switch.
- [x] Step 4: Surface provider contract fields and reserved GJT config fields.
- [x] Step 5: Run backend CRUD tests and frontend build.

### Task 3: Teacher Resource CRUD and Hierarchy

**Files:**
- Modify: `frontend/src/api/resources.ts`
- Modify: `frontend/src/views/teacher/ResourceCenter.vue`

- [x] Step 1: Add create/update/delete resource API helpers.
- [x] Step 2: Replace demo card-only resource center with real list hierarchy.
- [x] Step 3: Add resource detail drawer and create/edit dialog.
- [x] Step 4: Add delete confirmation and reload behavior.
- [x] Step 5: Run frontend build.

### Task 4: Project and Task Layer Cleanup

**Files:**
- Modify: `frontend/src/views/teacher/ProjectList.vue`
- Modify: `frontend/src/views/teacher/ProjectDetail.vue`

- [x] Step 1: Remove demo fallback from normal API success paths.
- [x] Step 2: Make empty states explicit instead of silently showing demo data.
- [x] Step 3: Ensure task create/edit/detail flow uses dialogs or drawers.
- [x] Step 4: Run frontend build.

### Task 5: Verification, Commit, and Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`

- [x] Step 1: Run backend compile/test verification.
- [x] Step 2: Run frontend build.
- [x] Step 3: Smoke test login, AI draft, AI progress, resource CRUD.
- [x] Step 4: Update progress document with verified results.
- [x] Step 5: Add remote `https://github.com/tanghaha258/jiaoping.git` if missing.
- [ ] Step 6: Commit and push branch `codex/agent-contract-crud`.
