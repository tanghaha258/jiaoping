# Trial Runbook Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add append-only rehearsal evidence records to the P11 trial operations runbook so administrators can record checked, blocked, or skipped stage rehearsals and see recent records on the Admin Dashboard.

**Architecture:** Reuse the existing `AuditLog` model as the first evidence store instead of adding a new table. Add small dashboard APIs that validate the six runbook stage keys, persist `trial_runbook.record` audit entries, and list recent records with the same paginated shape used elsewhere. The frontend extends the existing `/admin` runbook panel with a compact record dialog and recent-record strip; it does not add a new route or mutate readiness state.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, Pydantic request schemas, pytest with FastAPI `TestClient`, Vue 3, TypeScript, Element Plus, existing frontend route smoke and release scripts.

---

## File Structure

- Create `backend/tests/test_trial_runbook_records.py`: backend TDD coverage for creating/listing runbook records, role blocking, invalid stage, invalid status, and audit-log persistence.
- Create `backend/app/schemas/trial_runbook.py`: request schema for `TrialRunbookRecordCreate`, including status literal validation and note length cap.
- Modify `backend/app/services/dashboard_service.py`: add stage-key constants, AuditLog-backed create/list methods, record serialization, and school-admin scoping.
- Modify `backend/app/api/routers/dashboard.py`: add `POST /dashboard/trial-operations/stages/{stage_key}/records` and `GET /dashboard/trial-operations/records`.
- Modify `frontend/src/api/dashboard.ts`: add runbook record types and `createTrialRunbookRecord()` / `getTrialRunbookRecords()` API helpers.
- Modify `frontend/src/views/admin/AdminDashboard.vue`: add record dialog, stage-level record action, recent records strip, submit handling, and record loading.
- Create `backend/tests/test_admin_dashboard_runbook_records.py`: static frontend contract coverage for record UI anchors and API helper usage.
- Modify `scripts/check_frontend_route_smoke.py`: protect the new Admin Dashboard anchors in static route smoke.
- Modify `docs/superpowers/progress/2026-05-25-platform-progress.md`: update Phase 11 Batch 2 progress after every stage.
- Modify `docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md`: check off tasks and record observed command output as work completes.

---

### Task 1: Backend Red Tests for Runbook Evidence Records

**Files:**
- Create: `backend/tests/test_trial_runbook_records.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md`

- [x] **Step 1: Write the failing API tests**

Create `backend/tests/test_trial_runbook_records.py` with this content:

```python
from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str) -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_admin_can_create_and_list_trial_runbook_record():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        payload = {
            "status": "checked",
            "note": "Provider mock rehearsal is ready for the trial handover.",
            "evidence": ["AI Provider: mock (normal)", "Recent diagnostics: no blocking item"],
        }

        create_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/ai_provider_rehearsal/records",
            headers=headers,
            json=payload,
        )
        list_response = client.get(
            "/api/v1/dashboard/trial-operations/records"
            "?stage_key=ai_provider_rehearsal&page=1&page_size=5",
            headers=headers,
        )
        audit_response = client.get(
            "/api/v1/audit-logs?action=trial_runbook.record&target_type=trial_runbook_stage",
            headers=headers,
        )

    assert create_response.status_code == 200, create_response.text
    created = create_response.json()["data"]
    assert created["stage_key"] == "ai_provider_rehearsal"
    assert created["status"] == payload["status"]
    assert created["note"] == payload["note"]
    assert created["evidence"] == payload["evidence"]
    assert created["operator_id"]
    assert created["operator_name"]
    assert created["created_at"]

    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()["data"]
    assert listed["total"] >= 1
    assert listed["page"] == 1
    assert listed["page_size"] == 5
    assert any(item["id"] == created["id"] for item in listed["items"])

    assert audit_response.status_code == 200, audit_response.text
    audit_items = audit_response.json()["data"]["items"]
    matching_logs = [
        item for item in audit_items
        if item["target_id"] == "ai_provider_rehearsal"
        and item["detail"]["status"] == "checked"
    ]
    assert matching_logs


def test_school_admin_can_create_records_and_teacher_is_blocked():
    with TestClient(app) as client:
        school_admin_headers = _login(client, "schooladmin")
        teacher_headers = _login(client, "teacher001")

        school_admin_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=school_admin_headers,
            json={
                "status": "blocked",
                "note": "Upload directory check needs site confirmation.",
                "evidence": ["Service readiness: warning"],
            },
        )
        teacher_post_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=teacher_headers,
            json={"status": "checked", "note": "teacher should not write", "evidence": []},
        )
        teacher_list_response = client.get(
            "/api/v1/dashboard/trial-operations/records",
            headers=teacher_headers,
        )

    assert school_admin_response.status_code == 200, school_admin_response.text
    assert teacher_post_response.status_code == 403
    assert teacher_post_response.json()["code"] == 403001
    assert teacher_list_response.status_code == 403
    assert teacher_list_response.json()["code"] == 403001


def test_trial_runbook_records_validate_stage_status_and_note_length():
    with TestClient(app) as client:
        headers = _login(client, "admin")

        invalid_stage_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/unknown_stage/records",
            headers=headers,
            json={"status": "checked", "note": "bad stage", "evidence": []},
        )
        invalid_status_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=headers,
            json={"status": "done", "note": "bad status", "evidence": []},
        )
        long_note_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=headers,
            json={"status": "checked", "note": "x" * 501, "evidence": []},
        )

    assert invalid_stage_response.status_code == 400
    assert invalid_status_response.status_code == 422
    assert long_note_response.status_code == 422
```

- [x] **Step 2: Run the new backend test to verify the red state**

Run:

```powershell
python -m pytest backend/tests/test_trial_runbook_records.py -q
```

Expected: fail because `/api/v1/dashboard/trial-operations/stages/{stage_key}/records` and `/api/v1/dashboard/trial-operations/records` are not implemented yet. The likely first failures are 404 responses from the create/list endpoints.

Observed 2026-05-28: `python -m pytest backend/tests/test_trial_runbook_records.py -q` failed as expected (`3 failed`, 5 warnings). The create endpoint returned 404 `{"detail":"Not Found"}`, proving the test is red because the runbook evidence API is missing.

- [x] **Step 3: Update progress and commit the red tests**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Started P11 Batch 2 Task 1 backend TDD. Added failing `backend/tests/test_trial_runbook_records.py` coverage for creating/listing runbook rehearsal records, AuditLog persistence, school-admin access, teacher blocking, invalid stage, invalid status, and note length validation. Verified the red state with `python -m pytest backend/tests/test_trial_runbook_records.py -q` failing because the runbook record endpoints are not implemented yet.
```

Mark this task's checkboxes in this plan. Then run:

```powershell
git add backend/tests/test_trial_runbook_records.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md
git commit -m "Add trial runbook evidence red tests"
git push
```

Expected: commit and push succeed.

---

### Task 2: Backend AuditLog-Backed Evidence API

**Files:**
- Create: `backend/app/schemas/trial_runbook.py`
- Modify: `backend/app/services/dashboard_service.py`
- Modify: `backend/app/api/routers/dashboard.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md`

- [x] **Step 1: Add the request schema**

Create `backend/app/schemas/trial_runbook.py`:

```python
"""Schemas for trial operations runbook evidence records."""

from typing import Literal

from pydantic import BaseModel, Field


class TrialRunbookRecordCreate(BaseModel):
    """Payload for appending one runbook rehearsal record."""

    status: Literal["checked", "blocked", "skipped"]
    note: str = Field(default="", max_length=500)
    evidence: list[str] = Field(default_factory=list, max_length=8)
```

- [x] **Step 2: Add constants and serialization helpers**

In `backend/app/services/dashboard_service.py`, add imports near the existing model imports:

```python
from sqlalchemy.orm import joinedload

from app.models.audit_log import AuditLog
from app.services.audit_service import create_audit_log
```

Add these constants near the top of `DashboardService`:

```python
    TRIAL_RUNBOOK_STAGE_KEYS = {
        "service_readiness",
        "base_data",
        "account_access",
        "ai_provider_rehearsal",
        "teaching_workflow",
        "resource_and_backup",
    }
    TRIAL_RUNBOOK_RECORD_ACTION = "trial_runbook.record"
    TRIAL_RUNBOOK_RECORD_TARGET_TYPE = "trial_runbook_stage"
```

Add these helpers near the other private helpers:

```python
    @staticmethod
    def _validate_trial_runbook_stage(stage_key: str) -> None:
        if stage_key not in DashboardService.TRIAL_RUNBOOK_STAGE_KEYS:
            raise ValueError("未知的试运行演练阶段")

    @staticmethod
    def _normalize_record_evidence(evidence: list[str]) -> list[str]:
        normalized = []
        for item in evidence[:8]:
            text = str(item).strip()
            if text:
                normalized.append(text[:300])
        return normalized

    @staticmethod
    def _trial_runbook_record_to_dict(log: AuditLog) -> dict:
        detail = log.detail or {}
        return {
            "id": log.id,
            "stage_key": detail.get("stage_key") or log.target_id,
            "status": detail.get("status"),
            "note": detail.get("note") or "",
            "evidence": detail.get("evidence") or [],
            "operator_id": log.user_id,
            "operator_name": log.user.name if log.user else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
```

- [x] **Step 3: Add create/list service methods**

In `backend/app/services/dashboard_service.py`, add these public methods after `get_trial_operations_runbook()`:

```python
    @staticmethod
    async def create_trial_runbook_record(
        db: AsyncSession,
        user: User,
        stage_key: str,
        payload,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """Append one trial runbook rehearsal evidence record."""
        DashboardService._validate_trial_runbook_stage(stage_key)
        evidence = DashboardService._normalize_record_evidence(payload.evidence)
        detail = {
            "stage_key": stage_key,
            "status": payload.status,
            "note": payload.note.strip(),
            "evidence": evidence,
        }
        log = await create_audit_log(
            db=db,
            user_id=user.id,
            action=DashboardService.TRIAL_RUNBOOK_RECORD_ACTION,
            target_type=DashboardService.TRIAL_RUNBOOK_RECORD_TARGET_TYPE,
            target_id=stage_key,
            ip=ip,
            user_agent=user_agent,
            detail=detail,
        )
        if log is None:
            raise RuntimeError("试运行演练记录保存失败")
        log.user = user
        return DashboardService._trial_runbook_record_to_dict(log)

    @staticmethod
    async def list_trial_runbook_records(
        db: AsyncSession,
        user: User,
        stage_key: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """List recent runbook rehearsal evidence records."""
        if stage_key:
            DashboardService._validate_trial_runbook_stage(stage_key)

        query = (
            select(AuditLog)
            .options(joinedload(AuditLog.user))
            .where(AuditLog.action == DashboardService.TRIAL_RUNBOOK_RECORD_ACTION)
            .where(AuditLog.target_type == DashboardService.TRIAL_RUNBOOK_RECORD_TARGET_TYPE)
        )
        count_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == DashboardService.TRIAL_RUNBOOK_RECORD_ACTION)
            .where(AuditLog.target_type == DashboardService.TRIAL_RUNBOOK_RECORD_TARGET_TYPE)
        )

        if stage_key:
            query = query.where(AuditLog.target_id == stage_key)
            count_query = count_query.where(AuditLog.target_id == stage_key)

        if user.role == "school_admin" and user.school_id:
            query = query.join(User, AuditLog.user_id == User.id).where(User.school_id == user.school_id)
            count_query = count_query.join(User, AuditLog.user_id == User.id).where(User.school_id == user.school_id)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await db.execute(
            query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        )
        logs = result.unique().scalars().all()
        return {
            "items": [DashboardService._trial_runbook_record_to_dict(log) for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }
```

- [x] **Step 4: Add dashboard routes**

In `backend/app/api/routers/dashboard.py`, update imports:

```python
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from app.core.response import error_response, success_response
from app.schemas.trial_runbook import TrialRunbookRecordCreate
```

Add the routes after `get_trial_operations_runbook()`:

```python
@router.post("/trial-operations/stages/{stage_key}/records")
async def create_trial_runbook_record(
    stage_key: str,
    payload: TrialRunbookRecordCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Append one rehearsal evidence record for a trial operations stage."""
    try:
        data = await DashboardService.create_trial_runbook_record(
            db=db,
            user=current_user,
            stage_key=stage_key,
            payload=payload,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content=error_response(400001, str(exc)))
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content=error_response(500001, str(exc)))
    return success_response(data=data, message="试运行演练记录已保存")


@router.get("/trial-operations/records")
async def list_trial_runbook_records(
    stage_key: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """List recent rehearsal evidence records for the trial operations runbook."""
    try:
        data = await DashboardService.list_trial_runbook_records(
            db=db,
            user=current_user,
            stage_key=stage_key,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content=error_response(400001, str(exc)))
    return success_response(data=data, message="试运行演练记录已获取")
```

- [x] **Step 5: Run targeted backend checks**

Run:

```powershell
python -m pytest backend/tests/test_trial_runbook_records.py backend/tests/test_trial_operations_runbook.py backend/tests/test_trial_readiness.py -q
python -m compileall backend\app
```

Expected: all selected tests pass and backend compile succeeds.

Observed 2026-05-28: `python -m pytest backend/tests/test_trial_runbook_records.py backend/tests/test_trial_operations_runbook.py backend/tests/test_trial_readiness.py -q` passed (`10 passed`, 5 warnings). `python -m compileall backend\app` also passed.

- [x] **Step 6: Update progress and commit backend implementation**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Completed P11 Batch 2 backend runbook evidence API. Added `TrialRunbookRecordCreate`, `POST /api/v1/dashboard/trial-operations/stages/{stage_key}/records`, `GET /api/v1/dashboard/trial-operations/records`, AuditLog-backed append-only persistence, school-admin scoping, and validation for stage keys, status, and note length. Verified with `python -m pytest backend/tests/test_trial_runbook_records.py backend/tests/test_trial_operations_runbook.py backend/tests/test_trial_readiness.py -q` and `python -m compileall backend\app`.
```

Mark this task's checkboxes in this plan. Then run:

```powershell
git add backend/app/schemas/trial_runbook.py backend/app/services/dashboard_service.py backend/app/api/routers/dashboard.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md
git commit -m "Add trial runbook evidence endpoint"
git push
```

Expected: commit and push succeed.

---

### Task 3: Frontend Red Tests for Runbook Record UI

**Files:**
- Create: `backend/tests/test_admin_dashboard_runbook_records.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md`

- [x] **Step 1: Write the failing frontend static tests**

Create `backend/tests/test_admin_dashboard_runbook_records.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AdminDashboard.vue"
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_dashboard_api_exposes_trial_runbook_record_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TrialRunbookRecord",
        "TrialRunbookRecordCreate",
        "TrialRunbookRecordStatus",
        "createTrialRunbookRecord",
        "getTrialRunbookRecords",
        "/dashboard/trial-operations/records",
        "/dashboard/trial-operations/stages/${stageKey}/records",
    ]:
        assert label in text


def test_admin_dashboard_renders_runbook_record_workflow():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "最近演练记录",
        "记录演练",
        "演练结论",
        "保存记录",
        "createTrialRunbookRecord",
        "getTrialRunbookRecords",
        "recordDialogVisible",
        "recentRunbookRecords",
    ]:
        assert label in text


def test_route_smoke_protects_runbook_record_anchors():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in ["最近演练记录", "记录演练"]:
        assert label in text
```

- [x] **Step 2: Run the static tests to verify the red state**

Run:

```powershell
python -m pytest backend/tests/test_admin_dashboard_runbook_records.py -q
```

Expected: fail because the dashboard API helpers, dialog anchors, and route-smoke anchors are not implemented yet.

Observed 2026-05-28: `python -m pytest backend/tests/test_admin_dashboard_runbook_records.py -q` failed as expected (`3 failed`, 1 warning). The failures showed missing `TrialRunbookRecord`, missing `最近演练记录`, and missing route-smoke record anchors.

- [x] **Step 3: Update progress and commit the red tests**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Started P11 Batch 2 Task 3 frontend TDD. Added failing `backend/tests/test_admin_dashboard_runbook_records.py` coverage for dashboard record API helpers, `/admin` record dialog anchors, recent-record anchors, and route-smoke protection. Verified the red state with `python -m pytest backend/tests/test_admin_dashboard_runbook_records.py -q` failing because the runbook evidence UI is not implemented yet.
```

Mark this task's checkboxes in this plan. Then run:

```powershell
git add backend/tests/test_admin_dashboard_runbook_records.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md
git commit -m "Add trial runbook evidence UI red tests"
git push
```

Expected: commit and push succeed.

---

### Task 4: Frontend Runbook Evidence Recording UI

**Files:**
- Modify: `frontend/src/api/dashboard.ts`
- Modify: `frontend/src/views/admin/AdminDashboard.vue`
- Modify: `scripts/check_frontend_route_smoke.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md`

- [x] **Step 1: Add dashboard API types and helpers**

In `frontend/src/api/dashboard.ts`, add these types after the existing runbook types:

```ts
export type TrialRunbookRecordStatus = 'checked' | 'blocked' | 'skipped'

export interface TrialRunbookRecord {
  id: string
  stage_key: string
  status: TrialRunbookRecordStatus
  note: string
  evidence: string[]
  operator_id: string
  operator_name?: string
  created_at?: string
}

export interface TrialRunbookRecordCreate {
  status: TrialRunbookRecordStatus
  note: string
  evidence: string[]
}
```

Add these helpers after `getTrialOperationsRunbook()`:

```ts
export function createTrialRunbookRecord(
  stageKey: string,
  data: TrialRunbookRecordCreate
): Promise<ApiResponse<TrialRunbookRecord>> {
  return request.post(`/dashboard/trial-operations/stages/${stageKey}/records`, data)
}

export function getTrialRunbookRecords(params?: {
  stage_key?: string
  page?: number
  page_size?: number
}): Promise<ApiResponse<PaginatedResponse<TrialRunbookRecord>>> {
  return request.get('/dashboard/trial-operations/records', { params })
}
```

- [x] **Step 2: Add dashboard record state and handlers**

In `frontend/src/views/admin/AdminDashboard.vue`, update the dashboard API import:

```ts
import {
  createTrialRunbookRecord,
  getAIUsage,
  getDashboardOverview,
  getProjectTrends,
  getTrialOperationsRunbook,
  getTrialReadiness,
  getTrialRunbookRecords,
  type TrialOperationsRunbook,
  type TrialOperationsStage,
  type TrialReadiness,
  type TrialReadinessItemStatus,
  type TrialRunbookRecord,
  type TrialRunbookRecordCreate,
  type TrialRunbookRecordStatus
} from '@/api/dashboard'
```

Add an icon import with the existing Element Plus icons:

```ts
import { ArrowRight, DocumentChecked, Refresh } from '@element-plus/icons-vue'
```

Add state near `trialRunbook`:

```ts
const recentRunbookRecords = ref<TrialRunbookRecord[]>([])
const recordDialogVisible = ref(false)
const recordSubmitting = ref(false)
const selectedRunbookStage = ref<TrialOperationsStage | null>(null)
const recordForm = ref<TrialRunbookRecordCreate>({
  status: 'checked',
  note: '',
  evidence: []
})
```

Update `loadData()` to request records:

```ts
const [overviewRes, trendsRes, aiRes, readinessRes, runbookRes, recordsRes] = await Promise.all([
  getDashboardOverview(),
  getProjectTrends(),
  getAIUsage(),
  getTrialReadiness(),
  getTrialOperationsRunbook(),
  getTrialRunbookRecords({ page: 1, page_size: 6 })
])
recentRunbookRecords.value = recordsRes.data.items
```

Add handlers:

```ts
const openRecordDialog = (stage: TrialOperationsStage) => {
  selectedRunbookStage.value = stage
  recordForm.value = {
    status: stage.status === 'error' ? 'blocked' : 'checked',
    note: '',
    evidence: [...stage.evidence]
  }
  recordDialogVisible.value = true
}

const submitRunbookRecord = async () => {
  if (!selectedRunbookStage.value) return
  recordSubmitting.value = true
  try {
    await createTrialRunbookRecord(selectedRunbookStage.value.key, recordForm.value)
    ElMessage.success('演练记录已保存')
    recordDialogVisible.value = false
    const recordsRes = await getTrialRunbookRecords({ page: 1, page_size: 6 })
    recentRunbookRecords.value = recordsRes.data.items
  } catch (error) {
    ElMessage.error('演练记录保存失败')
  } finally {
    recordSubmitting.value = false
  }
}

const recordStatusText = (status: TrialRunbookRecordStatus) => {
  const map: Record<TrialRunbookRecordStatus, string> = {
    checked: '已检查',
    blocked: '有阻断',
    skipped: '已跳过'
  }
  return map[status]
}

const recordTagType = (status: TrialRunbookRecordStatus) => {
  const map: Record<TrialRunbookRecordStatus, 'success' | 'warning' | 'info'> = {
    checked: 'success',
    blocked: 'warning',
    skipped: 'info'
  }
  return map[status]
}

const stageTitle = (stageKey: string) => (
  trialRunbook.value.stages.find(stage => stage.key === stageKey)?.title || stageKey
)
```

- [x] **Step 3: Add record actions, recent strip, and dialog markup**

Inside each `.runbook-stage`, keep the existing route action and add the record action:

```vue
<div class="stage-actions">
  <el-button text type="primary" :icon="ArrowRight" @click="goTo(stage.route)">
    {{ stage.primary_action }}
  </el-button>
  <el-button text type="primary" :icon="DocumentChecked" @click="openRecordDialog(stage)">
    记录演练
  </el-button>
</div>
```

Add the recent records strip below the runbook stage list:

```vue
<div class="recent-runbook-records">
  <div class="recent-head">
    <h3>最近演练记录</h3>
    <span>{{ recentRunbookRecords.length }} 条</span>
  </div>
  <div v-if="recentRunbookRecords.length" class="record-list">
    <article v-for="record in recentRunbookRecords" :key="record.id" class="record-item">
      <div>
        <strong>{{ stageTitle(record.stage_key) }}</strong>
        <span>{{ record.operator_name || '管理员' }}</span>
      </div>
      <el-tag :type="recordTagType(record.status)" effect="light">
        {{ recordStatusText(record.status) }}
      </el-tag>
      <p>{{ record.note || '未填写备注' }}</p>
    </article>
  </div>
  <el-empty v-else description="暂无演练记录" :image-size="72" />
</div>
```

Add the dialog near the bottom of the template:

```vue
<el-dialog v-model="recordDialogVisible" title="记录演练" width="560px">
  <div v-if="selectedRunbookStage" class="record-dialog">
    <h3>{{ selectedRunbookStage.title }}</h3>
    <el-form label-position="top">
      <el-form-item label="演练结论">
        <el-radio-group v-model="recordForm.status">
          <el-radio-button label="checked">已检查</el-radio-button>
          <el-radio-button label="blocked">有阻断</el-radio-button>
          <el-radio-button label="skipped">已跳过</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="备注">
        <el-input
          v-model="recordForm.note"
          type="textarea"
          :rows="4"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      <el-form-item label="证据">
        <div class="dialog-evidence">
          <span v-for="item in recordForm.evidence" :key="item">{{ item }}</span>
        </div>
      </el-form-item>
    </el-form>
  </div>
  <template #footer>
    <el-button @click="recordDialogVisible = false">取消</el-button>
    <el-button type="primary" :loading="recordSubmitting" @click="submitRunbookRecord">
      保存记录
    </el-button>
  </template>
</el-dialog>
```

- [x] **Step 4: Add CSS and route smoke anchors**

In `frontend/src/views/admin/AdminDashboard.vue`, add compact styles:

```css
.stage-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recent-runbook-records {
  border-top: 1px solid #e4e7ed;
  margin-top: 16px;
  padding-top: 14px;
}

.recent-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.recent-head h3 {
  margin: 0;
  color: #1f2f5f;
  font-size: 15px;
}

.record-list {
  display: grid;
  gap: 8px;
}

.record-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px;
}

.record-item div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.record-item strong,
.record-dialog h3 {
  color: #1f2f5f;
  font-size: 14px;
}

.record-item p {
  margin: 8px 0 0;
  color: #606266;
  font-size: 13px;
}

.dialog-evidence {
  display: grid;
  gap: 6px;
}

.dialog-evidence span {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 8px;
  color: #303133;
  font-size: 13px;
}
```

In `scripts/check_frontend_route_smoke.py`, add `"最近演练记录"` and `"记录演练"` to the `/admin` anchors.

- [x] **Step 5: Run targeted frontend checks**

Run:

```powershell
python -m pytest backend/tests/test_admin_dashboard_runbook_records.py backend/tests/test_admin_dashboard_trial_ops.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
npm run build
```

Expected: all tests pass and frontend build succeeds.

Observed 2026-05-28: `python -m pytest backend/tests/test_admin_dashboard_runbook_records.py backend/tests/test_admin_dashboard_trial_ops.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q` passed (`12 passed`, 1 warning). `npm run build` passed with existing Rollup pure-comment, Sass legacy API, and chunk-size warnings.

- [x] **Step 6: Update progress and commit frontend implementation**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Completed P11 Batch 2 admin dashboard runbook evidence UI. Added dashboard API types and helpers for rehearsal records, a stage-level `记录演练` dialog, status/note/evidence submission, and a `最近演练记录` strip on `/admin`. Verified with `python -m pytest backend/tests/test_admin_dashboard_runbook_records.py backend/tests/test_admin_dashboard_trial_ops.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q` and `npm run build`.
```

Mark this task's checkboxes in this plan. Then run:

```powershell
git add frontend/src/api/dashboard.ts frontend/src/views/admin/AdminDashboard.vue scripts/check_frontend_route_smoke.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md
git commit -m "Add admin trial runbook evidence UI"
git push
```

Expected: commit and push succeed.

---

### Task 5: Release Verification and Browser Smoke

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md`

- [ ] **Step 1: Run the full release check**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-release.ps1
```

Expected: backend tests pass, backend compile passes, frontend text health passes, route smoke passes, and frontend build passes.

- [ ] **Step 2: Browser smoke `/admin`**

Start or reuse the local backend/frontend services. Open:

```text
http://127.0.0.1:3000/admin
```

Login as:

```text
username: admin
password: admin123
```

Verify:

- `/admin` renders `试运行演练台`, `记录演练`, and `最近演练记录`.
- Clicking `记录演练` opens the dialog.
- The dialog renders `演练结论`, `证据`, and `保存记录`.
- Saving a record closes the dialog and appends it to `最近演练记录`.
- Browser console has no new errors or warnings.

- [ ] **Step 3: Update progress and complete P11 Batch 2**

Update the Phase 11 checklist in `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- [x] Add runbook evidence record APIs and tests.
- [x] Add admin dashboard evidence recording UI.
- [x] Run release verification, browser smoke, commit, and push.
```

Add a completed-work entry:

```markdown
- 2026-05-28: Completed P11 Batch 2 release verification and browser smoke. `scripts/check-release.ps1` passed with backend tests, backend compile, frontend text health, route smoke, and frontend build. Browser smoke confirmed `/admin` can open `记录演练`, save an evidence record, and show it under `最近演练记录` without console errors.
```

Mark this task's checkboxes in this plan. Then run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-runbook-evidence.md
git commit -m "Verify trial runbook evidence"
git push
```

Expected: commit and push succeed.

---

## Self-Review

- Spec coverage: the plan covers append-only AuditLog evidence, the two dashboard endpoints, the three allowed record statuses, the six allowed stage keys, note length validation, school-admin scoping, teacher blocking, dashboard record UI, recent records, route smoke, release verification, browser smoke, progress updates, and push after every stage.
- Placeholder scan: no draft markers remain; every task has exact files, code, commands, and expected outcomes.
- Type consistency: backend uses `stage_key`, `status`, `note`, `evidence`, `operator_id`, `operator_name`, and `created_at`; frontend types and UI use the same field names.
- Scope check: P11 Batch 2 stays inside the existing Admin Dashboard and AuditLog model. It does not add a new navigation route, mutable readiness status, upstream Provider calls, or a dedicated reporting table.
