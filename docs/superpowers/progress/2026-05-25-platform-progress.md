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
- [ ] Verify, commit, and push.

## Decisions

- AI provider integration remains local-contract-first. GJT API details stay behind provider adapters.
- AI output never publishes directly to students. Teacher adoption is required.
- Thinking progress is stored per AI call so future external providers can stream/update the same model.
- Frontend modules should prefer list/detail/dialog hierarchy over single flat dashboards.

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
- 2026-05-25: Verified backend with `python -m pytest backend/tests -q` (`3 passed`) and `python -m compileall backend\app`.
- 2026-05-25: Verified frontend with `npm run build`.
- 2026-05-25: Smoke-tested API login, lesson-plan draft generation, AI progress retrieval, and resource create/update/delete through FastAPI `TestClient`.
