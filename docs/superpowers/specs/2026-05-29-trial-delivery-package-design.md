# P12 Trial Delivery Package Design

## Goal

Turn the trial-readiness and trial-operations evidence from P8-P11 into an administrator-facing delivery center. A school operator should be able to open the platform, review whether the pilot can be handed over, and copy or download a concise acceptance package for onsite review without stitching together screenshots and chat notes.

## Current State

- `/api/v1/dashboard/trial-readiness` returns live readiness items for service, organization data, user accounts, AI contract, workflow, student tasks, resources, and backup path.
- `/api/v1/dashboard/trial-operations/runbook` returns six ordered rehearsal stages.
- `/api/v1/dashboard/trial-operations/records` lists append-only AuditLog-backed rehearsal evidence.
- Admin dashboard already shows readiness, the rehearsal runbook, and recent rehearsal records.
- Organization and account import/export flows already exist under admin pages.
- Deployment and acceptance docs describe manual checks, demo accounts, the demo loop, and backup/restore expectations.

The gap is handover packaging. The platform has operational evidence, but there is no single product surface that turns it into a trial delivery package for a school administrator, onsite operator, or competition reviewer.

## Decision

Use the confirmed Approach B: add an in-platform delivery center plus downloadable materials.

The feature will add a dedicated admin route instead of further growing the dashboard:

- Frontend route: `/admin/trial-delivery`
- Backend route: `GET /api/v1/dashboard/trial-delivery/package`

The route is read-only in the first batch. It aggregates existing evidence and produces both structured JSON and a Markdown handover document. It does not introduce signatures, attachment uploads, external Provider calls, or a mutable acceptance workflow.

## Delivery Package Contract

The backend response should be deterministic and easy to render:

```json
{
  "status": "ready",
  "generated_at": "2026-05-29T10:00:00Z",
  "summary": {
    "readiness_ok": 8,
    "readiness_warning": 0,
    "readiness_error": 0,
    "runbook_checked": 4,
    "runbook_blocked": 0,
    "runbook_skipped": 1
  },
  "audience_sections": [
    {
      "key": "school_admin",
      "title": "学校管理员交付要点",
      "items": ["确认组织数据", "核对教师与学生账号", "保存初始密码发放清单"]
    }
  ],
  "acceptance_checklist": [
    {
      "key": "service_readiness",
      "title": "服务与数据可用",
      "status": "ok",
      "evidence": ["服务可用：数据库和上传目录正常"],
      "latest_record": {
        "status": "checked",
        "note": "现场演练通过",
        "operator_name": "系统管理员",
        "created_at": "2026-05-29T09:40:00Z"
      }
    }
  ],
  "demo_script": [
    {
      "step": 1,
      "role": "teacher",
      "title": "教师登录并打开项目",
      "route": "/teacher/projects",
      "expected_evidence": "能看到项目列表和跨学科任务入口"
    }
  ],
  "accounts": [
    {
      "role": "system_admin",
      "username": "admin",
      "password_hint": "见本地交付清单",
      "purpose": "查看交付包、readiness、AI Provider 和审计记录"
    }
  ],
  "materials": {
    "markdown": "# 试点交付包\n...",
    "json": "{...}"
  }
}
```

Allowed package status values:

- `ready`: no readiness errors and no latest runbook evidence marked as blocked.
- `action_required`: at least one readiness error or latest runbook blocked record exists.

Checklist item status values continue to use the existing readiness status set:

- `ok`
- `warning`
- `error`

Runbook evidence status values continue to use the P11 status set:

- `checked`
- `blocked`
- `skipped`

## Evidence Sources

### Readiness Evidence

Source:

- `DashboardService.get_trial_readiness(db)`

Use:

- Package status.
- Delivery summary counts.
- Acceptance checklist evidence.
- Action routes for unresolved items.

### Runbook Stage Evidence

Source:

- `DashboardService.get_trial_operations_runbook(db)`
- `DashboardService.list_trial_runbook_records(db, user, page_size=50)`

Use:

- Acceptance checklist rows mapped to the six runbook stages.
- Latest operator record per stage.
- Runbook evidence counters.
- Markdown evidence trail.

### Demo Accounts

Source:

- Seed/default local trial accounts documented in `backend/app/db/seed.py`.
- Current user list can be counted from the database, but plaintext passwords must not be read from hashes or exposed through API queries.

Use:

- The delivery package should include demo account usernames and role purpose.
- The API should label passwords as handout-controlled hints, not derive or expose stored hashes.
- Default local seed hints may appear only as documented local-trial material, with wording that they must be changed before real school use.

### Demo Script

Source:

- `11_测试与验收方案.md`
- Existing platform routes.

Use:

- Provide a concise onsite route sequence:
  - admin opens delivery package and readiness;
  - teacher opens project/workflow;
  - student opens tasks and submission;
  - teacher reviews and confirms evaluation;
  - admin inspects AI calls, audit logs, and runbook records.

## Backend Design

Add `DashboardService.get_trial_delivery_package(db, user)` beside the P11 methods.

Implementation principles:

- Reuse existing P8-P11 service methods instead of re-querying everything independently.
- Keep the response read-only and deterministic.
- Build one helper that converts the package to Markdown so API and frontend use the same wording.
- Do not expose password hashes, API keys, JWT secrets, Provider keys, raw request headers, or full AI payload bodies.
- Respect admin role boundaries. The endpoint uses the same roles as P11: `system_admin`, `school_admin`, and `region_admin`.
- School-admin record visibility follows the existing P11 AuditLog scoping.

Add router endpoint:

`GET /api/v1/dashboard/trial-delivery/package`

Response message should be concise and human-readable.

## Frontend Design

Add a dedicated admin page:

- `frontend/src/views/admin/TrialDeliveryPackage.vue`

Add admin route:

- `/admin/trial-delivery`

Add API types and helper in `frontend/src/api/dashboard.ts`:

- `TrialDeliveryPackage`
- `TrialDeliveryChecklistItem`
- `TrialDeliveryDemoStep`
- `getTrialDeliveryPackage()`

The page should be an operational work surface, not a landing page:

- Header with package status, generated time, and summary counts.
- Acceptance checklist grouped by runbook stage.
- Latest rehearsal record for each stage.
- Demo script section with role, route, action, and expected evidence.
- Demo account handout section with usernames, role purpose, and password-safety warning.
- Materials section with:
  - copy Markdown button;
  - download Markdown button;
  - download JSON button.

Expected visible anchors for static and browser smoke:

- `试点交付包`
- `现场验收清单`
- `演示脚本`
- `测试账号交付`
- `下载 Markdown`
- `下载 JSON`
- `复制交付材料`

Navigation can be added to the admin menu or linked from the admin dashboard quick actions. The route smoke must protect the page either way.

## Download Behavior

The frontend should download generated materials client-side from the API response:

- Markdown file name: `trial-delivery-package.md`
- JSON file name: `trial-delivery-package.json`

The backend does not need streaming file endpoints in Batch 1. This keeps the implementation simple and avoids filesystem cleanup.

## Error Handling

- Backend aggregation errors should return a clear 500 and not partially expose internal exception details.
- Unknown or malformed AuditLog details should be skipped defensively in evidence aggregation.
- Missing runbook records should not block package generation; the checklist should show "尚无演练记录" for that stage.
- Frontend loading failure should show an Element Plus error message and a retry action.
- Clipboard copy failure should show a readable message and leave the Markdown visible for manual selection.

## Non-Goals

- No electronic signature or acceptance approval workflow in Batch 1.
- No file attachment upload for signed acceptance forms.
- No PDF generation; Markdown is enough for the first handover package.
- No external Provider rehearsal trigger.
- No mutation of readiness, runbook records, user accounts, or organization data.
- No exposure of secrets or plaintext passwords from stored user records.

## Testing Strategy

Use TDD for implementation:

1. Backend red tests for package shape, role access, readiness/runbook evidence inclusion, demo account safety wording, and blocked-state status.
2. Backend implementation in `DashboardService` and dashboard router.
3. Frontend static red tests for API helper, route, and visible anchors.
4. Frontend implementation of the delivery page and client-side downloads.
5. Release verification and browser smoke on `/admin/trial-delivery`.

## Release Criteria

P12 Batch 1 is complete when:

- Admin roles can load the trial delivery package.
- Teachers and students cannot load the package.
- The package includes readiness evidence, runbook stage evidence, latest rehearsal records, demo script steps, and safe account handout guidance.
- `/admin/trial-delivery` renders the acceptance checklist, demo script, account handout, and material actions.
- Markdown and JSON downloads work from the browser.
- Static route smoke, targeted tests, full release check, and browser smoke pass.
- Progress docs are updated, committed, and pushed after each stage.

## Proposed P12 Breakdown

### Batch 1: Delivery Package MVP

- Backend package contract and tests.
- Read-only package aggregation endpoint.
- Admin delivery page with copy/download actions.
- Release verification and browser smoke.

### Batch 2: Onsite Acceptance Enhancements

- Add printable acceptance wording and fallback procedure sections.
- Add role-specific handout blocks for operator, teacher, student, and reviewer.
- Consider a signed-form upload or acceptance record only after real pilot feedback confirms the need.
