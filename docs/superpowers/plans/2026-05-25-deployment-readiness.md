# Deployment Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deployment readiness checks, environment examples, scripts, and documentation so the platform can be started, checked, and smoke-tested for a school trial.

**Architecture:** Keep the existing FastAPI + Vue + Nginx/Docker architecture. Add small operational endpoints to the existing health router and keep deployment scripts outside business modules.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest, Vite/Vue, PowerShell, Python standard library smoke checks.

---

## File Structure

- Modify `backend/app/api/routers/health.py` for liveness/readiness endpoint behavior.
- Create `backend/tests/test_deployment_readiness.py` for TDD coverage of health endpoints and deployment artifacts.
- Create `backend/.env.example` and `frontend/.env.example` for deployment configuration.
- Create `scripts/start-local.ps1`, `scripts/check-release.ps1`, and `scripts/smoke_deploy.py`.
- Create `docs/DEPLOYMENT.md` for local and Docker trial operation.
- Modify `docs/superpowers/progress/2026-05-25-platform-progress.md` after each milestone.

## Tasks

### Task 1: Health and Artifact Tests

**Files:**
- Create: `backend/tests/test_deployment_readiness.py`

- [x] Write failing tests for `/api/v1/health`, `/api/v1/health/ready`, env examples, scripts, and deployment docs.
- [x] Run `python -m pytest backend/tests/test_deployment_readiness.py -q` and confirm failures are for missing readiness/artifacts.

### Task 2: Readiness Endpoints

**Files:**
- Modify: `backend/app/api/routers/health.py`

- [x] Implement `GET /api/v1/health` with `service`, `version`, and `environment`.
- [x] Implement `GET /api/v1/health/ready` with database, upload directory, seed data, and AI provider checks.
- [x] Run `python -m pytest backend/tests/test_deployment_readiness.py -q` and confirm endpoint tests pass while artifact tests still guide remaining work.

### Task 3: Env Examples, Scripts, and Deployment Docs

**Files:**
- Create: `backend/.env.example`
- Create: `frontend/.env.example`
- Create: `scripts/start-local.ps1`
- Create: `scripts/check-release.ps1`
- Create: `scripts/smoke_deploy.py`
- Create: `docs/DEPLOYMENT.md`

- [x] Add backend and frontend environment examples with current supported keys.
- [x] Add local start and release-check PowerShell scripts.
- [x] Add Python smoke script that checks health/readiness and optionally authenticates.
- [x] Add deployment docs for local trial and Docker trial.
- [x] Run `python -m pytest backend/tests/test_deployment_readiness.py -q`.

### Task 4: Full Verification and Handoff

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`

- [x] Update progress tracker with Phase 4 status.
- [x] Run `python -m pytest backend/tests -q`.
- [x] Run `python -m compileall backend\app`.
- [x] Run `npm run build` in `frontend`.
- [x] Run `python scripts/smoke_deploy.py` against the running API when available.
- [x] Run `git diff --check`.
- [ ] Commit and push `codex/agent-contract-crud`.
