# Trial Delivery Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete P12 Batch 2 by turning the trial delivery package into onsite-ready handover material with printable acceptance wording, fallback procedures, and role-specific handoff cards.

**Architecture:** Keep the delivery package read-only and continue reusing the dashboard aggregation endpoint. The backend adds three deterministic material blocks to the existing `GET /api/v1/dashboard/trial-delivery/package` response; the frontend renders those blocks on `/admin/trial-delivery` and the existing Markdown/JSON downloads include them automatically.

**Tech Stack:** FastAPI, existing `DashboardService`, Vue 3, Element Plus, static pytest checks, route smoke, release verification.

---

## Scope Guard

Included:

- `printable_acceptance`: concise wording for printing or pasting into an onsite acceptance form.
- `fallback_procedures`: operator-facing steps for no-network, Provider unavailable, account access, and backup/restore scenarios.
- `role_handoffs`: role-specific checklists for platform admin, school admin, teacher, student, and reviewer.
- Markdown output sections for the new material.
- Frontend sections and static route smoke anchors.
- Progress update, release verification, browser smoke, commit, and push.

Excluded:

- No signed-form upload.
- No mutable acceptance status.
- No PDF generation.
- No Provider rehearsal trigger.
- No account password exposure.

## Files

- Modify: `backend/tests/test_trial_delivery_package.py`
  - Add backend contract assertions for the three new read-only material blocks.
- Modify: `backend/tests/test_trial_delivery_page.py`
  - Add frontend static assertions for the new types and visible anchors.
- Modify: `backend/app/services/dashboard_service.py`
  - Add constants/helpers for printable acceptance wording, fallback procedures, role handoff cards, and Markdown sections.
- Modify: `frontend/src/api/dashboard.ts`
  - Add TypeScript interfaces for the new material blocks.
- Modify: `frontend/src/views/admin/TrialDeliveryPackage.vue`
  - Render the new sections below the current delivery grid.
- Modify: `scripts/check_frontend_route_smoke.py`
  - Protect the new visible anchors.
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
  - Track Batch 2 completion and close P12.

## Task 1: Backend Contract

- [x] Add failing assertions to `backend/tests/test_trial_delivery_package.py`:
  - package includes `printable_acceptance`, `fallback_procedures`, and `role_handoffs`;
  - printable acceptance includes `title`, `purpose`, `required_signoffs`, and statements;
  - fallback procedures include owner, trigger, steps, and evidence;
  - role handoffs include required roles and checklist items;
  - Markdown includes `打印验收说明`, `异常处置流程`, and `分角色交接卡`;
  - no password hashes or secrets appear.
- [x] Run `python -m pytest backend/tests/test_trial_delivery_package.py -q`; expected red failure on missing keys.
- [x] Add minimal backend implementation in `DashboardService`.
- [x] Re-run `python -m pytest backend/tests/test_trial_delivery_package.py -q`; expected green.

## Task 2: Frontend Contract

- [x] Add failing static assertions to `backend/tests/test_trial_delivery_page.py` for new TypeScript interfaces and visible anchors:
  - `TrialDeliveryPrintableAcceptance`
  - `TrialDeliveryFallbackProcedure`
  - `TrialDeliveryRoleHandoff`
  - `打印验收说明`
  - `异常处置流程`
  - `分角色交接卡`
- [x] Run `python -m pytest backend/tests/test_trial_delivery_page.py -q`; expected red failure on missing types/anchors.
- [x] Add TypeScript interfaces and render the new sections on `TrialDeliveryPackage.vue`.
- [x] Update route smoke anchors.
- [x] Re-run `python -m pytest backend/tests/test_trial_delivery_page.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q`; expected green.

## Task 3: Release Closeout

- [x] Run `powershell -ExecutionPolicy Bypass -File scripts/check-release.ps1`.
- [x] Browser-smoke `/admin/trial-delivery` as `admin` and confirm the new anchors render with zero console errors/warnings.
- [x] Update progress doc and mark Phase 12 complete.
- [x] Commit and push.

## Self-Review

- Spec coverage: Implements the Batch 2 onsite acceptance enhancements from the P12 design without adding mutable workflows.
- Placeholder scan: No placeholders or deferred implementation details.
- Type consistency: Backend keys and frontend interfaces use the same names: `printable_acceptance`, `fallback_procedures`, and `role_handoffs`.
