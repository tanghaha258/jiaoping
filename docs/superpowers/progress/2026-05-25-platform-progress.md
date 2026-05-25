# 2026-05-25 Platform Development Progress

## Current Goal

Build an operational AI-agent-driven teaching-assessment workflow platform:

- External AI agents are accessed through local contracts first.
- AI generation has observable thinking/progress stages.
- Modules use hierarchy, detail drawers/dialogs, and real CRUD.
- Work is verified before completion and pushed to `tanghaha258/jiaoping`.

## Progress Log

- [x] Installed and enabled obra/superpowers globally.
- [x] Reframed the goal around agent contracts, module hierarchy, and real CRUD.
- [x] Created branch `codex/agent-contract-crud`.
- [x] Wrote this implementation plan and progress tracker.
- [x] Implement AI contract and thinking progress backend.
- [x] Implement admin AI agent CRUD UI.
- [x] Implement teacher resource CRUD UI.
- [x] Clean project/task hierarchy and demo fallbacks.
- [x] Verify backend and frontend build.
- [x] Browser-smoke teacher login and key teacher pages.
- [x] Commit and push.
- [x] Phase 2: Complete student submission and teacher evaluation loop.
  - [x] Backend TDD for student submission list, confirmed feedback visibility, and cross-student access blocking.
  - [x] Teacher submission review workbench.
  - [x] Teacher evaluation ledger.
  - [x] Student task and feedback UI.
  - [x] Phase 2 verification, commit, and push.
- [x] Phase 3: Complete admin operations base data and ledgers.
  - [x] Backend TDD for organization CRUD, system settings, user management, and role blocking.
  - [x] Admin user management page.
  - [x] Admin school/class/subject/region management page.
  - [x] Admin settings, audit log, and AI call ledger pages.
  - [x] Phase 3 verification, browser smoke, commit, and push.
- [x] Phase 4: Harden deployment readiness for trial operation.
  - [x] Added liveness/readiness health contract design and implementation plan.
  - [x] Added backend readiness checks for database, uploads, seed data, and AI provider mode.
  - [x] Added backend/frontend environment examples.
  - [x] Added local start, release-check, and deployment smoke scripts.
  - [x] Added local and Docker trial deployment documentation.
  - [x] Verified Phase 4 readiness tests.
- [x] Phase 5: Add trial account password operations.
  - [x] Added self-service password change contract and tests.
  - [x] Added system-admin password reset contract and tests.
  - [x] Added teacher settings password form.
  - [x] Added admin user reset-password dialog.
- [x] Phase 6: Add organization data portability for trial setup.
  - [x] Added non-destructive JSON organization data package contract.
  - [x] Added template, export, dry-run import, and committed import APIs.
  - [x] Added repeated-import skip behavior and role blocking tests.
  - [x] Added school-management UI controls for template/export/import.
- [x] Phase 7: Add user account portability for trial setup.
  - [x] Added non-destructive JSON teacher/student account package contract.
  - [x] Added template, export, dry-run import, and committed import APIs.
  - [x] Added initial-password handout list for newly created accounts only.
  - [x] Added user-management UI controls for template/export/import.

## Decisions

- AI provider integration remains local-contract-first. GJT API details stay behind provider adapters.
- AI output never publishes directly to students. Teacher adoption is required.
- Thinking progress is stored per AI call so future external providers can stream/update the same model.
- Frontend modules should prefer list/detail/dialog hierarchy over single flat dashboards.
- Phase 2 prioritizes the post-adoption teaching-assessment loop before expanding new AI scenarios.
- Organization data import is additive and non-destructive: existing region/school/class/subject data is skipped, not overwritten or deleted.
- User account import is additive and non-destructive: existing usernames are skipped, existing passwords are never exported, and initial passwords are only returned for accounts created by the current import.

## Completed Work

- 2026-05-25: Added local AI scenario contracts through `/api/v1/ai/contracts`.
- 2026-05-25: Added `AICallStep` and `/api/v1/ai/calls/{call_id}/progress` for agent thinking/progress tracking.
- 2026-05-25: Lesson-plan draft generation now records the five standard thinking steps: understanding, retrieving_context, drafting, normalizing, awaiting_review.
- 2026-05-25: Verified with `python -m pytest backend/tests/test_ai_contract_progress.py -q` (`2 passed`).
- 2026-05-25: Added AI agent soft-delete API and verified with `python -m pytest backend/tests/test_ai_agent_crud.py -q` (`1 passed`).
- 2026-05-25: Rebuilt admin AI agent config as real CRUD UI with filters, detail drawer, create/edit dialog, enable switch, delete action, local contract panel, and GJT reserved fields.
- 2026-05-25: Verified frontend with `npm run build`.
- 2026-05-25: Rebuilt teacher resource center as real CRUD UI with hierarchy tree, filters, list, detail drawer, create/edit dialog, delete confirmation, and reload behavior.
- 2026-05-25: Removed normal-path demo fallbacks from project list/detail and task list; empty states now show explicitly.
- 2026-05-25: Added task detail drawer and edit dialog in project detail.
- 2026-05-25: Rebuilt project list and project detail as clean Chinese operational pages with explicit state actions.
- 2026-05-25: Aligned task type selections with backend enums (`individual`, `group`, `classroom`, `homework`) so manual task CRUD uses real API values.
- 2026-05-25: Added operational smoke tests for resource metadata CRUD, lesson-plan adoption, duplicate adoption blocking, and student-side draft-task invisibility.
- 2026-05-25: Verified backend with `python -m pytest backend/tests -q` (`5 passed`) and `python -m compileall backend\app`.
- 2026-05-25: Verified frontend with `npm run build`.
- 2026-05-25: Smoke-tested API login, lesson-plan draft generation, AI progress retrieval, and resource create/update/delete through FastAPI `TestClient`.
- 2026-05-25: Browser-smoked teacher UI on `http://127.0.0.1:3000`: login, project list, resource center, and AI lesson-plan workflow page render with normal Chinese text and expected workflow content.
- 2026-05-25: Committed and pushed branch `codex/agent-contract-crud` to `https://github.com/tanghaha258/jiaoping.git`.
- 2026-05-25: Started Phase 2 design and plan for student submissions, teacher submission review, evaluation ledger, and student feedback visibility.
- 2026-05-25: Added backend regression test for the student submission -> teacher confirmed evaluation -> student feedback loop, including cross-student submission and evaluation detail blocking.
- 2026-05-25: Fixed student submission list service wiring and scoped confirmed evaluations to the owning student.
- 2026-05-25: Verified Phase 2 backend loop with `python -m pytest backend/tests/test_student_feedback_flow.py -q` (`1 passed`).
- 2026-05-25: Added real `evaluator_type` API filtering for the evaluation ledger.
- 2026-05-25: Rebuilt teacher submission review with real task/submission/rubric/evaluation APIs, detail drawer, and teacher-evaluation dialog.
- 2026-05-25: Rebuilt teacher evaluation center as a real ledger with status/evaluator filters, detail drawer, and confirm action.
- 2026-05-25: Rebuilt student task list, task detail, and submission detail around real submissions and confirmed feedback cards.
- 2026-05-25: Added backend guards for student resubmission: existing submissions update through `PATCH /submissions/{id}`, and closed tasks reject resubmission.
- 2026-05-25: Verified Phase 2 with `python -m pytest backend/tests -q` (`8 passed`), `python -m compileall backend\app`, and `npm run build`.
- 2026-05-25: Restarted the local backend to clear an old 8000-port instance, then Edge-smoked the full loop: teacher task publish, student submit, teacher review page, evaluation ledger, confirm feedback, and student feedback/detail pages.
- 2026-05-25: Tightened student task status semantics so `pending/submitted/reviewed` filter by the student's own submission/confirmed-feedback state, not the task publish state.
- 2026-05-25: Re-ran verification after the semantics fix: `python -m pytest backend/tests -q` (`8 passed`), `python -m compileall backend\app`, `npm run build`, and Edge full-loop smoke.
- 2026-05-25: Moved submission `reviewed` state to evaluation confirmation, so draft evaluations remain teacher-only until explicitly confirmed.
- 2026-05-25: Re-ran Edge full-loop smoke after restarting the current backend: teacher published task, student submitted, teacher created/confirmed evaluation, and student feedback pages showed the confirmed feedback.
- 2026-05-25: Started Phase 3 admin operations for deployable base-data maintenance and operational ledgers.
- 2026-05-25: Added `/api/v1/org/*` organization APIs for regions, schools, classes, and subjects.
- 2026-05-25: Added `/api/v1/settings` JSON settings APIs and keyword search for user lists.
- 2026-05-25: Rebuilt admin user management, school management, system settings, audit logs, AI call history, and admin dashboard with real APIs and readable Chinese copy.
- 2026-05-25: Verified Phase 3 backend with `python -m pytest backend/tests/test_admin_operations.py -q` (`3 passed`) and all backend tests with `python -m pytest backend/tests -q` (`11 passed`).
- 2026-05-25: Verified frontend with `npm run build` and Edge-smoked admin dashboard, users, schools, settings, audit logs, and AI calls pages.
- 2026-05-25: Started Phase 4 deployment readiness hardening.
- 2026-05-25: Added `GET /api/v1/health/ready` with database, upload directory, core seed-data, and AI provider-mode checks.
- 2026-05-25: Added `backend/.env.example`, `frontend/.env.example`, `scripts/start-local.ps1`, `scripts/check-release.ps1`, `scripts/smoke_deploy.py`, and `docs/DEPLOYMENT.md`.
- 2026-05-25: Verified Phase 4 TDD with `python -m pytest backend/tests/test_deployment_readiness.py -q` (`3 passed`).
- 2026-05-25: Verified Phase 4 full release path with `python -m pytest backend/tests -q` (`14 passed`), `python -m compileall backend\app`, `npm run build`, `python scripts\smoke_deploy.py`, and `powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1`.
- 2026-05-25: Started Phase 5 account security hardening for trial operation.
- 2026-05-25: Added password-change and admin reset-password backend tests, then implemented `/api/v1/auth/change-password` and `/api/v1/users/{user_id}/reset-password`.
- 2026-05-25: Verified Phase 5 backend with `python -m pytest backend/tests/test_account_security.py -q` (`3 passed`).
- 2026-05-25: Added teacher password form and admin reset-password dialog, then verified with `npm run build`.
- 2026-05-25: Started Phase 6 organization data portability for trial setup.
- 2026-05-25: Added organization data package tests for template, export, dry-run import, committed import, repeated import skip, and non-admin blocking.
- 2026-05-25: Implemented `/api/v1/org/data/template`, `/api/v1/org/data/export`, and `/api/v1/org/data/import`.
- 2026-05-25: Verified Phase 6 backend with `python -m pytest backend/tests/test_org_data_portability.py -q` (`2 passed`).
- 2026-05-25: Added school-management controls for template download, data export, dry-run import, and committed import; verified with `npm run build`.
- 2026-05-25: Started Phase 7 user account portability for trial setup.
- 2026-05-25: Added user account package tests for template, password-redacted export, dry-run import, committed import, student class binding, repeated import skip, login with imported password, and non-admin blocking.
- 2026-05-25: Verified Phase 7 backend with `python -m pytest backend/tests/test_user_account_portability.py -q` (`3 passed`).
- 2026-05-25: Added user-management controls for account template download, account export, dry-run import, committed import, import summary, and newly created account password handout list; verified with `npm run build`.
