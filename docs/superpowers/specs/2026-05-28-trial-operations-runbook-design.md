# P11 Batch 1 Trial Operations Runbook Design

## Goal

Start Phase 11 by turning the existing trial-readiness checklist into an administrator-facing operations runbook. A school or platform operator should be able to open the Admin Dashboard, see which trial stage needs attention, follow a concrete action route, and inspect the evidence behind each stage before the platform is handed to real teachers and students.

## Current State

- `/api/v1/dashboard/trial-readiness` already returns live readiness items for service health, organization data, user accounts, AI contract readiness, teaching workflow, student tasks, resources, and backup path.
- `/admin` already renders the readiness checklist with quick actions.
- P10 added provider-neutral AI diagnostics, real-provider configuration risk detection, and `/admin/ai-calls` failure diagnosis.
- Import/export flows exist for organization data and user accounts.
- Backup and restore scripts exist for local SQLite trial operation.

The gap is operational sequencing. Administrators can see individual readiness items, but they do not yet have a stage-by-stage rehearsal view that says what to do first, what route to open, what evidence confirms success, and where provider rehearsal sits in the wider trial workflow.

## Approaches Considered

### A. Dashboard-Centered Runbook

Extend the existing dashboard with a compact "试运行演练台" panel and a backend endpoint that groups readiness evidence into operational stages.

Benefits:

- Uses the existing admin entry point and readiness service.
- Low routing and navigation cost.
- Easy to test with current backend and static route smoke patterns.
- Keeps P11 focused on trial operations rather than a new product surface.

Trade-off: the dashboard becomes denser, so the UI must remain compact and scan-friendly.

### B. Dedicated `/admin/trial-ops` Route

Add a new route for trial operations.

Benefits:

- Cleaner separation for a future larger operations center.
- More room for logs, rehearsals, and historical records.

Trade-off: adds menu, route, and page surface before there is enough unique workflow to justify it. It also duplicates readiness context from the dashboard.

### C. AI-Agent-Only Rehearsal

Extend `/admin/ai-agents` and `/admin/ai-calls` with provider rehearsal guidance only.

Benefits:

- Strong focus on P10 provider work.
- Minimal backend scope.

Trade-off: misses organization data, accounts, teaching workflow, resources, and backup readiness. P11 needs the full trial loop, not only AI.

## Decision

Use Approach A for P11 Batch 1. Build a dashboard-centered operations runbook backed by one read-only admin endpoint:

`GET /api/v1/dashboard/trial-operations/runbook`

The endpoint will not call external AI providers, mutate setup data, generate lesson plans, or store secrets. It will aggregate existing platform evidence and return stage guidance for administrators.

## Runbook Contract

The response should be deterministic and easy to render:

```json
{
  "status": "ready",
  "checked_at": "2026-05-28T10:00:00Z",
  "summary": {
    "ok": 5,
    "warning": 1,
    "error": 0
  },
  "stages": [
    {
      "key": "service_readiness",
      "title": "服务与数据可用",
      "status": "ok",
      "owner": "平台管理员",
      "route": "/admin",
      "primary_action": "查看 readiness",
      "evidence": ["readiness: 服务可用"],
      "next_step": "确认本地服务、数据库和上传目录可用后进入基础数据检查。"
    }
  ]
}
```

Allowed status values:

- `ok`: evidence is sufficient for trial rehearsal.
- `warning`: rehearsal can continue, but the operator should address the item before real handover.
- `error`: the stage blocks trial rehearsal.

Required stage keys for Batch 1:

- `service_readiness`
- `base_data`
- `account_access`
- `ai_provider_rehearsal`
- `teaching_workflow`
- `resource_and_backup`

## Stage Mapping

### Service Readiness

Input evidence:

- Existing readiness item `service_readiness`.

Output:

- Route: `/admin`
- Owner: `平台管理员`
- Action: check dashboard readiness and release check evidence.

### Base Data

Input evidence:

- Existing readiness item `organization_data`.

Output:

- Route: `/admin/schools`
- Owner: `区县/学校管理员`
- Action: import or verify regions, schools, classes, and subjects.

### Account Access

Input evidence:

- Existing readiness item `user_accounts`.

Output:

- Route: `/admin/users`
- Owner: `学校管理员`
- Action: import or verify teacher/student accounts and initial-password handout readiness.

### AI Provider Rehearsal

Input evidence:

- Existing readiness item `ai_contract`.
- P10 AI diagnostics summary when available.

Output:

- Route: `/admin/ai-agents` for configuration blockers.
- Route: `/admin/ai-calls` when recent runtime failures are the primary risk.
- Owner: `平台管理员`
- Action: run local readiness self-checks, inspect recent failures, and keep mock/manual mode acceptable until real Provider credentials are ready.

This stage must keep the provider-neutral principle: 桂教通 and other domestic providers are adapters behind the local contract, not platform core assumptions.

### Teaching Workflow

Input evidence:

- Existing readiness items `teaching_workflow` and `student_task_availability`.

Output:

- Route: `/teacher/projects`
- Owner: `试点教师`
- Action: confirm at least one project/task loop can be demonstrated from teacher creation through student availability.

### Resource and Backup

Input evidence:

- Existing readiness items `resources` and `backup_path`.

Output:

- Route: `/teacher/resources` when resource material is the main gap.
- Route: `/admin` when backup readiness is the main gap.
- Owner: `平台管理员`
- Action: verify resource seed material and SQLite backup/restore script availability.

## Backend Design

Add `DashboardService.get_trial_operations_runbook(db)` beside `get_trial_readiness`. It should reuse the readiness result rather than re-querying every module independently. A small mapping layer will convert readiness items into six runbook stages, merge status severity, and preserve evidence strings.

The new router path should use the same admin roles as `/dashboard/trial-readiness`:

- `system_admin`
- `school_admin`
- `region_admin`

Teachers and students must receive 403.

## Frontend Design

Extend `frontend/src/api/dashboard.ts` with the runbook types and `getTrialOperationsRunbook()`.

Update `frontend/src/views/admin/AdminDashboard.vue`:

- Load runbook data with the existing dashboard requests.
- Add a compact "试运行演练台" section near the readiness checklist.
- Render stage status, owner, evidence, next step, and a route button.
- Keep the current readiness checklist intact.
- Use dense operational layout, not a landing page or marketing hero.

Expected visible anchors for smoke/static checks:

- `试运行演练台`
- `演练阶段`
- `责任角色`
- `证据`
- `下一步`
- `Provider演练`

## Error Handling

- If runbook loading fails, the dashboard should show an Element Plus error message and preserve the rest of the dashboard fallback state.
- Backend should return an empty-but-valid stage list only if readiness has no items, which is not expected after seeded data. The normal path should always include the six stage keys.
- No endpoint in this batch should expose secrets or upstream request bodies.

## Testing Strategy

Use TDD:

1. Backend API tests for admin access, role blocking, response shape, required stage keys, and AI-provider route selection.
2. Backend service tests through public API only, reusing seeded data and existing failure fixtures where practical.
3. Frontend static tests for dashboard anchors and API route usage.
4. Route smoke updates if new visible anchors need protection.
5. Release verification through `scripts/check-release.ps1`.
6. Browser smoke for `/admin` after the frontend implementation.

## Release Criteria

P11 Batch 1 is complete when:

- `GET /api/v1/dashboard/trial-operations/runbook` returns six ordered stages for admin roles.
- Non-admin roles are blocked.
- `/admin` shows the runbook without removing the existing readiness checklist.
- The AI Provider stage links administrators to provider configuration or AI call diagnostics according to the current risk.
- Targeted tests, release checks, and browser smoke pass.
- Progress docs and implementation plan are updated, committed, and pushed at each stage.
