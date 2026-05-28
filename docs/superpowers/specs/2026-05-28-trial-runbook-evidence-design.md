# P11 Batch 2 Trial Runbook Evidence Design

## Goal

Add lightweight rehearsal evidence for the P11 trial operations runbook. Administrators should be able to mark a runbook stage as checked, blocked, or skipped, leave an operator note, and later see recent rehearsal records without creating a large new operations module.

## Current State

- P11 Batch 1 added `GET /api/v1/dashboard/trial-operations/runbook`.
- `/admin` now renders the stage-by-stage `试运行演练台`.
- The platform already has append-only `AuditLog` records with `action`, `target_type`, `target_id`, `detail`, and `created_at`.
- `/admin/audit-logs` can list audit logs, but the runbook panel does not yet show rehearsal-specific history or let admins record a stage check.

## Problem

The runbook tells an operator what to rehearse, but after a rehearsal there is no concise evidence trail that says:

- who checked a stage;
- which stage was checked;
- whether it passed, was blocked, or was skipped;
- what evidence/status existed at that moment;
- what note the operator left for handover.

Without this, trial acceptance still depends on screenshots or chat messages outside the platform.

## Approaches Considered

### A. Reuse AuditLog for Runbook Evidence

Create a small dashboard endpoint that appends an `AuditLog` action such as `trial_runbook.record` with `target_type="trial_runbook_stage"`.

Benefits:

- No schema migration.
- Uses existing append-only audit semantics.
- Easy to list/filter through existing audit infrastructure.
- Good fit for Batch 2 because evidence is operator-entered, not a business object workflow.

Trade-off: records are stored in generic `detail` JSON, so richer reporting later may need a dedicated table.

### B. Add Dedicated `trial_runbook_records` Table

Add a new model and CRUD endpoints for runbook evidence.

Benefits:

- Stronger typed columns and future reporting.
- Easier to query by status/stage/operator without JSON detail access.

Trade-off: more schema and UI surface for a small first evidence loop. This is better after trial sites confirm what record fields they actually need.

### C. Store Evidence in System Settings

Keep latest runbook notes in a JSON setting.

Benefits:

- Very fast to build.
- No new endpoint category.

Trade-off: settings are mutable, not append-only; this weakens auditability and makes handover history easy to overwrite.

## Decision

Use Approach A for P11 Batch 2. Add a lightweight AuditLog-backed evidence API under the dashboard router:

- `POST /api/v1/dashboard/trial-operations/stages/{stage_key}/records`
- `GET /api/v1/dashboard/trial-operations/records`

The API should be append-only. It must not mutate readiness state, run upstream Provider calls, or store secrets.

## Evidence Contract

### Create Record

Request:

```json
{
  "status": "checked",
  "note": "服务、基础数据和 Provider mock 演练均可继续。",
  "evidence": ["AI Provider: mock（正常）"]
}
```

Allowed status values:

- `checked`
- `blocked`
- `skipped`

Response:

```json
{
  "id": "audit-log-id",
  "stage_key": "ai_provider_rehearsal",
  "status": "checked",
  "note": "服务、基础数据和 Provider mock 演练均可继续。",
  "evidence": ["AI Provider: mock（正常）"],
  "operator_id": "user-admin-000000-0000-0000-0001",
  "operator_name": "系统管理员",
  "created_at": "2026-05-28T10:00:00Z"
}
```

### List Records

`GET /api/v1/dashboard/trial-operations/records?stage_key=ai_provider_rehearsal&page=1&page_size=10`

Response uses the existing paginated shape:

```json
{
  "items": [
    {
      "id": "audit-log-id",
      "stage_key": "ai_provider_rehearsal",
      "status": "checked",
      "note": "服务、基础数据和 Provider mock 演练均可继续。",
      "evidence": ["AI Provider: mock（正常）"],
      "operator_id": "user-admin-000000-0000-0000-0001",
      "operator_name": "系统管理员",
      "created_at": "2026-05-28T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

## Stage Validation

Only the six Batch 1 stage keys are accepted:

- `service_readiness`
- `base_data`
- `account_access`
- `ai_provider_rehearsal`
- `teaching_workflow`
- `resource_and_backup`

Unknown stage keys should return 400.

## Backend Design

Add small methods to `DashboardService`:

- `create_trial_runbook_record(db, user, stage_key, payload)`
- `list_trial_runbook_records(db, user, stage_key, page, page_size)`

Implementation details:

- Use `create_audit_log(...)`.
- `action`: `trial_runbook.record`
- `target_type`: `trial_runbook_stage`
- `target_id`: `stage_key`
- `detail`: `{"stage_key": ..., "status": ..., "note": ..., "evidence": [...]}`
- Serialize through one helper so POST and GET return the same shape.
- School admin visibility follows existing audit-log school filtering through the user relation. Since system admin seed user has no school, system admins see all runbook records.

## Frontend Design

Keep the evidence UI inside the existing dashboard runbook panel:

- Add a small "记录演练" action per stage.
- Open an Element Plus dialog with:
  - stage title;
  - status segmented/radio control: checked, blocked, skipped;
  - textarea note;
  - readonly evidence list from the stage;
  - submit/cancel buttons.
- Add a compact "最近演练记录" strip under the runbook panel:
  - stage title/status;
  - operator;
  - note preview;
  - created time.

This stays operational and dense. No new landing page, menu item, or standalone route is needed in Batch 2.

## Error Handling

- Invalid `stage_key` returns 400 with a readable message.
- Invalid `status` returns 422 through request validation.
- Notes should be capped at 500 characters.
- Evidence should be capped to a small list and stored as plain strings.
- Audit creation failure should return a clear 500 because this endpoint's only purpose is to persist evidence.
- The frontend should show a message on save failure and keep the dialog open.

## Testing Strategy

Use TDD:

1. Backend red tests for record creation, listing, role blocking, invalid stage, and note/evidence persistence.
2. Backend implementation using AuditLog.
3. Frontend static red tests for API types, dashboard dialog anchors, and route smoke anchors.
4. Frontend implementation.
5. Release verification and browser smoke on `/admin`.

## Release Criteria

P11 Batch 2 is complete when:

- Admin roles can append runbook stage records.
- Teachers/students cannot append or list records.
- Recent records can be listed globally or by stage.
- `/admin` lets operators record a stage rehearsal and see recent records.
- All targeted tests, release checks, and browser smoke pass.
- Progress docs are updated, committed, and pushed after each stage.
