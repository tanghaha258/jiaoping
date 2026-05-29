# Trial Delivery Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build P12 Batch 1: a read-only trial delivery package that aggregates readiness, runbook, rehearsal evidence, demo script, and safe account handout material into an admin page with Markdown/JSON downloads.

**Architecture:** Reuse the existing dashboard aggregation layer rather than creating a new domain module. The backend adds one admin-only package endpoint under `/api/v1/dashboard/trial-delivery/package`; the frontend adds a dedicated `/admin/trial-delivery` page and client-side copy/download actions.

**Tech Stack:** FastAPI, SQLAlchemy async, existing AuditLog-backed runbook records, Vue 3, Element Plus, Vite, pytest, static route smoke scripts.

---

## Scope Guard

This plan implements only P12 Batch 1 from `docs/superpowers/specs/2026-05-29-trial-delivery-package-design.md`.

Included:

- Admin-only read API for the trial delivery package.
- Readiness, runbook, and recent rehearsal record aggregation.
- Safe demo account handout guidance without exposing password hashes or stored secrets.
- Dedicated `/admin/trial-delivery` page.
- Markdown and JSON client-side downloads.
- Route smoke, targeted tests, release verification, browser smoke, progress update, commit, and push.

Excluded:

- Electronic signature workflow.
- Signed acceptance attachment upload.
- PDF generation.
- External Provider rehearsal trigger.
- Any mutation of readiness, runbook records, users, organization data, or settings.
- Teacher menu real-page cleanup. Record it as P13 risk, but do not implement it during P12 Batch 1.

## Files

- Create: `backend/tests/test_trial_delivery_package.py`
  - Backend contract tests for the package endpoint.
- Create: `backend/tests/test_trial_delivery_page.py`
  - Static frontend contract tests for API helper, route, menu, page anchors, and route smoke coverage.
- Modify: `backend/app/services/dashboard_service.py`
  - Add `get_trial_delivery_package(...)` and private helpers for status, checklist, demo script, safe accounts, Markdown, and JSON material generation.
- Modify: `backend/app/api/routers/dashboard.py`
  - Add `GET /trial-delivery/package`.
- Modify: `frontend/src/api/dashboard.ts`
  - Add package TypeScript types and `getTrialDeliveryPackage()`.
- Modify: `frontend/src/router/routes.ts`
  - Add `/admin/trial-delivery`.
- Modify: `frontend/src/layouts/RoleMenu.vue`
  - Add admin menu entry and available root for `/admin/trial-delivery`.
- Create: `frontend/src/views/admin/TrialDeliveryPackage.vue`
  - Render package status, checklist, latest records, demo script, account handout, and material actions.
- Modify: `scripts/check_frontend_route_smoke.py`
  - Protect `/admin/trial-delivery` route and anchors.
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
  - Track P12 Batch 1 task progress and final verification.

---

## Task 1: Backend Red Tests

**Files:**

- Create: `backend/tests/test_trial_delivery_package.py`

- [ ] **Step 1: Create backend contract tests**

Create `backend/tests/test_trial_delivery_package.py` with this content:

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


def test_admin_can_view_trial_delivery_package():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        response = client.get("/api/v1/dashboard/trial-delivery/package", headers=headers)

    assert response.status_code == 200, response.text
    package = response.json()["data"]

    assert package["status"] in {"ready", "action_required"}
    assert package["generated_at"]
    assert package["summary"]["readiness_ok"] >= 0
    assert package["summary"]["readiness_warning"] >= 0
    assert package["summary"]["readiness_error"] >= 0
    assert package["summary"]["runbook_checked"] >= 0
    assert package["summary"]["runbook_blocked"] >= 0
    assert package["summary"]["runbook_skipped"] >= 0

    checklist_keys = {item["key"] for item in package["acceptance_checklist"]}
    assert checklist_keys == {
        "service_readiness",
        "base_data",
        "account_access",
        "ai_provider_rehearsal",
        "teaching_workflow",
        "resource_and_backup",
    }
    for item in package["acceptance_checklist"]:
        assert item["title"]
        assert item["status"] in {"ok", "warning", "error"}
        assert item["route"]
        assert isinstance(item["evidence"], list)
        assert "latest_record" in item

    assert any(step["route"] == "/teacher/projects" for step in package["demo_script"])
    assert any(step["route"] == "/student/tasks" for step in package["demo_script"])
    assert any(step["route"] == "/admin/ai-calls" for step in package["demo_script"])

    account_usernames = {item["username"] for item in package["accounts"]}
    assert {"admin", "schooladmin", "teacher001", "student001"}.issubset(account_usernames)
    for account in package["accounts"]:
        assert "password_hash" not in account
        assert "password" not in account
        assert account["password_hint"]
        assert "正式试点前必须重置" in account["password_hint"]

    assert package["materials"]["markdown"].startswith("# 试点交付包")
    assert "现场验收清单" in package["materials"]["markdown"]
    assert "演示脚本" in package["materials"]["markdown"]
    assert "测试账号交付" in package["materials"]["markdown"]
    assert "\"acceptance_checklist\"" in package["materials"]["json"]


def test_school_admin_can_view_delivery_package_and_teacher_is_blocked():
    with TestClient(app) as client:
        school_admin_headers = _login(client, "schooladmin")
        teacher_headers = _login(client, "teacher001")

        school_admin_response = client.get(
            "/api/v1/dashboard/trial-delivery/package",
            headers=school_admin_headers,
        )
        teacher_response = client.get(
            "/api/v1/dashboard/trial-delivery/package",
            headers=teacher_headers,
        )

    assert school_admin_response.status_code == 200, school_admin_response.text
    assert teacher_response.status_code == 403
    assert teacher_response.json()["code"] == 403001


def test_blocked_runbook_record_marks_delivery_package_action_required():
    note = "P12 delivery package blocked evidence marker"
    with TestClient(app) as client:
        headers = _login(client, "admin")
        record_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/ai_provider_rehearsal/records",
            headers=headers,
            json={
                "status": "blocked",
                "note": note,
                "evidence": ["Provider rehearsal blocked for package test"],
            },
        )
        package_response = client.get(
            "/api/v1/dashboard/trial-delivery/package",
            headers=headers,
        )

    assert record_response.status_code == 200, record_response.text
    assert package_response.status_code == 200, package_response.text
    package = package_response.json()["data"]
    provider_item = next(
        item for item in package["acceptance_checklist"]
        if item["key"] == "ai_provider_rehearsal"
    )
    assert package["status"] == "action_required"
    assert package["summary"]["runbook_blocked"] >= 1
    assert provider_item["latest_record"]["status"] == "blocked"
    assert provider_item["latest_record"]["note"] == note
    assert "Provider rehearsal blocked for package test" in package["materials"]["markdown"]
```

- [ ] **Step 2: Run backend red tests**

Run:

```powershell
python -m pytest backend/tests/test_trial_delivery_package.py -q
```

Expected: fail because `/api/v1/dashboard/trial-delivery/package` does not exist yet. The response should include `404` or an assertion failure on status code.

- [ ] **Step 3: Commit backend red tests**

Run:

```powershell
git add backend/tests/test_trial_delivery_package.py
git commit -m "Add trial delivery package backend red tests"
git push
```

- [ ] **Step 4: Update progress after Task 1**

Add a completed-work entry to `docs/superpowers/progress/2026-05-25-platform-progress.md` saying P12 Batch 1 backend red tests were added and the expected red state was verified.

Run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Record trial delivery backend red state"
git push
```

---

## Task 2: Backend Delivery Package Endpoint

**Files:**

- Modify: `backend/app/services/dashboard_service.py`
- Modify: `backend/app/api/routers/dashboard.py`
- Test: `backend/tests/test_trial_delivery_package.py`

- [ ] **Step 1: Add imports and constants in `dashboard_service.py`**

Add `json` to imports:

```python
import json
```

Add these constants inside `DashboardService`, below `TRIAL_RUNBOOK_RECORD_TARGET_TYPE`:

```python
    TRIAL_DELIVERY_DEMO_SCRIPT = [
        {
            "step": 1,
            "role": "system_admin",
            "title": "管理员打开试点交付包",
            "route": "/admin/trial-delivery",
            "expected_evidence": "能看到现场验收清单、演示脚本、测试账号交付和下载材料。",
        },
        {
            "step": 2,
            "role": "teacher",
            "title": "教师打开跨学科项目",
            "route": "/teacher/projects",
            "expected_evidence": "能看到项目列表、项目详情和课时任务入口。",
        },
        {
            "step": 3,
            "role": "teacher",
            "title": "教师进入 AI 教学方案",
            "route": "/teacher/ai/lesson-plan",
            "expected_evidence": "能生成或查看待审阅的 AI 教学方案草案，并保持教师采纳门槛。",
        },
        {
            "step": 4,
            "role": "student",
            "title": "学生查看学习任务",
            "route": "/student/tasks",
            "expected_evidence": "能看到已发布任务并进入任务详情。",
        },
        {
            "step": 5,
            "role": "teacher",
            "title": "教师审阅提交并确认评价",
            "route": "/teacher/evaluations",
            "expected_evidence": "能查看评价记录，确认后的反馈对学生可见。",
        },
        {
            "step": 6,
            "role": "system_admin",
            "title": "管理员核验 AI 调用和审计证据",
            "route": "/admin/ai-calls",
            "expected_evidence": "能查看 AI 调用观测、失败诊断和调用台账。",
        },
    ]

    TRIAL_DELIVERY_ACCOUNTS = [
        {
            "role": "system_admin",
            "username": "admin",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "查看交付包、readiness、AI Provider、审计日志和系统设置。",
        },
        {
            "role": "school_admin",
            "username": "schooladmin",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "核对学校、班级、教师学生账号和试运行演练记录。",
        },
        {
            "role": "teacher",
            "username": "teacher001",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "演示项目、任务、AI 教学方案、提交审阅和评价确认。",
        },
        {
            "role": "student",
            "username": "student001",
            "password_hint": "见本地账号交付清单；正式试点前必须重置。",
            "purpose": "演示学习任务查看、作品提交和反馈查看。",
        },
    ]
```

- [ ] **Step 2: Add public service method**

Add this method after `list_trial_runbook_records(...)`:

```python
    @staticmethod
    async def get_trial_delivery_package(db: AsyncSession, user: User) -> dict:
        """Build a read-only handover package from readiness and rehearsal evidence."""
        readiness = await DashboardService.get_trial_readiness(db)
        runbook = await DashboardService.get_trial_operations_runbook(db)
        records = await DashboardService.list_trial_runbook_records(
            db=db,
            user=user,
            page=1,
            page_size=50,
        )
        latest_by_stage = DashboardService._latest_runbook_records_by_stage(records["items"])
        checklist = [
            DashboardService._trial_delivery_checklist_item(stage, latest_by_stage.get(stage["key"]))
            for stage in runbook["stages"]
        ]
        record_summary = DashboardService._trial_delivery_record_summary(records["items"])
        summary = {
            "readiness_ok": readiness["summary"]["ok"],
            "readiness_warning": readiness["summary"]["warning"],
            "readiness_error": readiness["summary"]["error"],
            **record_summary,
        }
        status = DashboardService._trial_delivery_status(readiness, checklist)

        package = {
            "status": status,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "audience_sections": DashboardService._trial_delivery_audience_sections(),
            "acceptance_checklist": checklist,
            "demo_script": DashboardService.TRIAL_DELIVERY_DEMO_SCRIPT,
            "accounts": DashboardService.TRIAL_DELIVERY_ACCOUNTS,
        }
        package["materials"] = {
            "markdown": DashboardService._trial_delivery_markdown(package),
            "json": json.dumps(package, ensure_ascii=False, indent=2),
        }
        return package
```

- [ ] **Step 3: Add private helpers**

Add these helpers before `_count(...)`:

```python
    @staticmethod
    def _latest_runbook_records_by_stage(records: list[dict]) -> dict[str, dict]:
        latest: dict[str, dict] = {}
        for record in records:
            stage_key = record.get("stage_key")
            if stage_key and stage_key not in latest:
                latest[stage_key] = record
        return latest

    @staticmethod
    def _trial_delivery_record_summary(records: list[dict]) -> dict:
        return {
            "runbook_checked": sum(1 for record in records if record.get("status") == "checked"),
            "runbook_blocked": sum(1 for record in records if record.get("status") == "blocked"),
            "runbook_skipped": sum(1 for record in records if record.get("status") == "skipped"),
        }

    @staticmethod
    def _trial_delivery_checklist_item(stage: dict, latest_record: Optional[dict]) -> dict:
        return {
            "key": stage["key"],
            "title": stage["title"],
            "status": stage["status"],
            "route": stage["route"],
            "owner": stage["owner"],
            "primary_action": stage["primary_action"],
            "evidence": stage["evidence"],
            "next_step": stage["next_step"],
            "latest_record": latest_record,
        }

    @staticmethod
    def _trial_delivery_status(readiness: dict, checklist: list[dict]) -> str:
        if readiness["summary"]["error"]:
            return "action_required"
        if any((item.get("latest_record") or {}).get("status") == "blocked" for item in checklist):
            return "action_required"
        if any(item["status"] == "error" for item in checklist):
            return "action_required"
        return "ready"

    @staticmethod
    def _trial_delivery_audience_sections() -> list[dict]:
        return [
            {
                "key": "operator",
                "title": "平台管理员交付要点",
                "items": ["检查 readiness", "下载交付材料", "核对 AI Provider 和审计证据"],
            },
            {
                "key": "school_admin",
                "title": "学校管理员交付要点",
                "items": ["确认组织数据", "核对教师与学生账号", "保存初始密码发放清单"],
            },
            {
                "key": "reviewer",
                "title": "评委验收要点",
                "items": ["查看完整教学闭环", "查看 AI 使用证据", "查看安全和权限边界"],
            },
        ]

    @staticmethod
    def _trial_delivery_markdown(package: dict) -> str:
        lines = [
            "# 试点交付包",
            "",
            f"- 生成时间：{package['generated_at']}",
            f"- 状态：{'可交付' if package['status'] == 'ready' else '需要处理'}",
            f"- readiness：正常 {package['summary']['readiness_ok']} / 提醒 {package['summary']['readiness_warning']} / 阻断 {package['summary']['readiness_error']}",
            f"- 演练记录：已检查 {package['summary']['runbook_checked']} / 阻断 {package['summary']['runbook_blocked']} / 已跳过 {package['summary']['runbook_skipped']}",
            "",
            "## 现场验收清单",
            "",
        ]
        for item in package["acceptance_checklist"]:
            latest = item.get("latest_record")
            latest_text = "尚无演练记录"
            if latest:
                latest_text = f"{latest.get('status')} / {latest.get('operator_name') or '管理员'} / {latest.get('note') or '未填写备注'}"
            lines.extend([
                f"### {item['title']}",
                f"- 状态：{DashboardService._status_label(item['status'])}",
                f"- 责任角色：{item['owner']}",
                f"- 处理入口：{item['route']}",
                f"- 最新演练：{latest_text}",
                "- 证据：",
            ])
            for evidence in item["evidence"]:
                lines.append(f"  - {evidence}")
            if latest and latest.get("evidence"):
                lines.append("- 演练补充证据：")
                for evidence in latest["evidence"]:
                    lines.append(f"  - {evidence}")
            lines.append("")

        lines.extend(["## 演示脚本", ""])
        for step in package["demo_script"]:
            lines.append(
                f"{step['step']}. [{step['role']}] {step['title']}：{step['route']}；验收证据：{step['expected_evidence']}"
            )

        lines.extend(["", "## 测试账号交付", ""])
        for account in package["accounts"]:
            lines.append(
                f"- {account['role']} / {account['username']}：{account['purpose']}（{account['password_hint']}）"
            )

        lines.extend(["", "## 交付提醒", "", "- 本材料不包含密码哈希、API Key、JWT Secret 或 Provider 密钥。", "- 正式试点前必须完成测试账号密码重置。"])
        return "\n".join(lines)
```

- [ ] **Step 4: Add router endpoint**

In `backend/app/api/routers/dashboard.py`, add this endpoint after `list_trial_runbook_records(...)`:

```python
@router.get("/trial-delivery/package")
async def get_trial_delivery_package(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Get the read-only onsite trial delivery package."""
    data = await DashboardService.get_trial_delivery_package(db=db, user=current_user)
    return success_response(data=data, message="Trial delivery package generated")
```

- [ ] **Step 5: Run backend tests**

Run:

```powershell
python -m pytest backend/tests/test_trial_delivery_package.py backend/tests/test_trial_runbook_records.py backend/tests/test_trial_operations_runbook.py backend/tests/test_trial_readiness.py -q
python -m compileall backend\app
```

Expected: all selected tests pass and backend app compiles.

- [ ] **Step 6: Commit backend implementation**

Run:

```powershell
git add backend/app/services/dashboard_service.py backend/app/api/routers/dashboard.py backend/tests/test_trial_delivery_package.py
git commit -m "Add trial delivery package endpoint"
git push
```

- [ ] **Step 7: Update progress after Task 2**

Add a completed-work entry to `docs/superpowers/progress/2026-05-25-platform-progress.md` summarizing the backend endpoint and verification output.

Run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Record trial delivery backend endpoint"
git push
```

---

## Task 3: Frontend Red Tests

**Files:**

- Create: `backend/tests/test_trial_delivery_page.py`
- Modify: `scripts/check_frontend_route_smoke.py`

- [ ] **Step 1: Create static frontend red tests**

Create `backend/tests/test_trial_delivery_page.py` with this content:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTES = ROOT / "frontend" / "src" / "router" / "routes.ts"
ROLE_MENU = ROOT / "frontend" / "src" / "layouts" / "RoleMenu.vue"
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "TrialDeliveryPackage.vue"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_dashboard_api_exposes_trial_delivery_package_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TrialDeliveryPackage",
        "TrialDeliveryChecklistItem",
        "TrialDeliveryDemoStep",
        "TrialDeliveryAccount",
        "getTrialDeliveryPackage",
        "/dashboard/trial-delivery/package",
    ]:
        assert label in text


def test_admin_route_and_menu_include_trial_delivery_page():
    routes = ROUTES.read_text(encoding="utf-8")
    role_menu = ROLE_MENU.read_text(encoding="utf-8")

    for label in [
        "path: 'trial-delivery'",
        "TrialDeliveryPackage",
        "试点交付包",
    ]:
        assert label in routes

    for label in [
        "/admin/trial-delivery",
        "试点交付包",
    ]:
        assert label in role_menu


def test_trial_delivery_page_renders_package_workflow():
    assert PAGE.exists(), f"Missing page: {PAGE}"
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "试点交付包",
        "现场验收清单",
        "演示脚本",
        "测试账号交付",
        "复制交付材料",
        "下载 Markdown",
        "下载 JSON",
        "getTrialDeliveryPackage",
        "downloadMarkdown",
        "downloadJson",
        "copyMarkdown",
    ]:
        assert label in text


def test_route_smoke_protects_trial_delivery_page():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in [
        "path: 'trial-delivery'",
        "TrialDeliveryPackage.vue",
        "试点交付包",
        "现场验收清单",
        "下载 Markdown",
    ]:
        assert label in text
```

- [ ] **Step 2: Run frontend red tests**

Run:

```powershell
python -m pytest backend/tests/test_trial_delivery_page.py -q
```

Expected: fail because the API types, route, page, menu entry, and route smoke expectation are not implemented yet.

- [ ] **Step 3: Commit frontend red tests**

Run:

```powershell
git add backend/tests/test_trial_delivery_page.py
git commit -m "Add trial delivery page red tests"
git push
```

- [ ] **Step 4: Update progress after Task 3**

Add a completed-work entry to `docs/superpowers/progress/2026-05-25-platform-progress.md` saying P12 frontend red tests were added and verified red.

Run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Record trial delivery frontend red state"
git push
```

---

## Task 4: Frontend Delivery Page

**Files:**

- Modify: `frontend/src/api/dashboard.ts`
- Modify: `frontend/src/router/routes.ts`
- Modify: `frontend/src/layouts/RoleMenu.vue`
- Create: `frontend/src/views/admin/TrialDeliveryPackage.vue`
- Modify: `scripts/check_frontend_route_smoke.py`
- Test: `backend/tests/test_trial_delivery_page.py`

- [ ] **Step 1: Add TypeScript API types and helper**

In `frontend/src/api/dashboard.ts`, add these interfaces after `TrialRunbookRecordCreate`:

```ts
export type TrialDeliveryPackageStatus = 'ready' | 'action_required'

export interface TrialDeliverySummary {
  readiness_ok: number
  readiness_warning: number
  readiness_error: number
  runbook_checked: number
  runbook_blocked: number
  runbook_skipped: number
}

export interface TrialDeliveryAudienceSection {
  key: string
  title: string
  items: string[]
}

export interface TrialDeliveryLatestRecord {
  id: string
  stage_key: string
  status: TrialRunbookRecordStatus
  note: string
  evidence: string[]
  operator_id: string
  operator_name?: string
  created_at?: string
}

export interface TrialDeliveryChecklistItem {
  key: string
  title: string
  status: TrialReadinessItemStatus
  route: string
  owner: string
  primary_action: string
  evidence: string[]
  next_step: string
  latest_record?: TrialDeliveryLatestRecord | null
}

export interface TrialDeliveryDemoStep {
  step: number
  role: string
  title: string
  route: string
  expected_evidence: string
}

export interface TrialDeliveryAccount {
  role: string
  username: string
  password_hint: string
  purpose: string
}

export interface TrialDeliveryPackage {
  status: TrialDeliveryPackageStatus
  generated_at: string
  summary: TrialDeliverySummary
  audience_sections: TrialDeliveryAudienceSection[]
  acceptance_checklist: TrialDeliveryChecklistItem[]
  demo_script: TrialDeliveryDemoStep[]
  accounts: TrialDeliveryAccount[]
  materials: {
    markdown: string
    json: string
  }
}
```

Add this API function after `getTrialRunbookRecords(...)`:

```ts
export function getTrialDeliveryPackage(): Promise<ApiResponse<TrialDeliveryPackage>> {
  return request.get('/dashboard/trial-delivery/package')
}
```

- [ ] **Step 2: Add admin route**

In `frontend/src/router/routes.ts`, add this child under the `/admin` children after the dashboard route:

```ts
      {
        path: 'trial-delivery',
        name: 'TrialDeliveryPackage',
        component: () => import('@/views/admin/TrialDeliveryPackage.vue'),
        meta: { title: '试点交付包' }
      },
```

- [ ] **Step 3: Add admin menu entry**

In `frontend/src/layouts/RoleMenu.vue`, add an admin menu item after the dashboard item:

```ts
        { index: '/admin/trial-delivery', label: '试点交付包', icon: Tickets, actionable: true },
```

In `handleSelect(...)`, include the new root:

```ts
'/admin/trial-delivery'
```

The final `availableRoots` list must include:

```ts
const availableRoots = ['/teacher', '/teacher/ai/lesson-plan', '/teacher/projects', '/teacher/evaluations', '/student', '/student/tasks', '/student/profile', '/research', '/research/templates', '/research/resources', '/admin', '/admin/trial-delivery', '/admin/users', '/admin/schools', '/admin/ai-agents', '/admin/ai-calls', '/admin/audit-logs', '/admin/settings']
```

- [ ] **Step 4: Create `TrialDeliveryPackage.vue`**

Create `frontend/src/views/admin/TrialDeliveryPackage.vue` with this structure:

```vue
<template>
  <div class="trial-delivery-page">
    <section class="header-band">
      <div>
        <p class="eyebrow">试运行交付</p>
        <h1>试点交付包</h1>
        <p>把 readiness、演练记录、演示脚本和测试账号交付材料汇总成现场验收清单。</p>
      </div>
      <div class="header-actions">
        <el-tag :type="packageStatusTag" effect="dark">
          {{ packageData.status === 'ready' ? '可交付' : '需要处理' }}
        </el-tag>
        <el-button :icon="Refresh" :loading="loading" @click="loadPackage">刷新</el-button>
      </div>
    </section>

    <section class="summary-grid">
      <article v-for="item in summaryCards" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.hint }}</em>
      </article>
    </section>

    <section class="delivery-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">现场验收清单</p>
          <h2>现场验收清单</h2>
        </div>
      </div>
      <el-table :data="packageData.acceptance_checklist" border>
        <el-table-column label="阶段" min-width="170">
          <template #default="{ row }">
            <strong>{{ row.title }}</strong>
            <p class="muted">{{ row.owner }}</p>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="light">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="证据" min-width="240">
          <template #default="{ row }">
            <div class="evidence-list">
              <span v-for="item in row.evidence" :key="item">{{ item }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="最新演练" min-width="220">
          <template #default="{ row }">
            <div v-if="row.latest_record" class="record-note">
              <el-tag :type="recordTag(row.latest_record.status)" effect="light">
                {{ recordText(row.latest_record.status) }}
              </el-tag>
              <span>{{ row.latest_record.operator_name || '管理员' }}</span>
              <p>{{ row.latest_record.note || '未填写备注' }}</p>
            </div>
            <span v-else class="muted">尚无演练记录</span>
          </template>
        </el-table-column>
        <el-table-column label="入口" width="140" align="center">
          <template #default="{ row }">
            <el-button text type="primary" :icon="ArrowRight" @click="go(row.route)">
              {{ row.primary_action }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="delivery-grid">
      <article class="delivery-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">演示脚本</p>
            <h2>演示脚本</h2>
          </div>
        </div>
        <ol class="script-list">
          <li v-for="step in packageData.demo_script" :key="step.step">
            <strong>{{ step.step }}. {{ step.title }}</strong>
            <span>{{ step.role }} · {{ step.route }}</span>
            <p>{{ step.expected_evidence }}</p>
          </li>
        </ol>
      </article>

      <article class="delivery-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">测试账号交付</p>
            <h2>测试账号交付</h2>
          </div>
        </div>
        <div class="account-list">
          <div v-for="account in packageData.accounts" :key="account.username" class="account-item">
            <strong>{{ account.username }}</strong>
            <span>{{ account.role }}</span>
            <p>{{ account.purpose }}</p>
            <em>{{ account.password_hint }}</em>
          </div>
        </div>
      </article>
    </section>

    <section class="delivery-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">交付材料</p>
          <h2>交付材料</h2>
        </div>
        <div class="material-actions">
          <el-button :icon="CopyDocument" @click="copyMarkdown">复制交付材料</el-button>
          <el-button :icon="Download" @click="downloadMarkdown">下载 Markdown</el-button>
          <el-button type="primary" :icon="Download" @click="downloadJson">下载 JSON</el-button>
        </div>
      </div>
      <el-input v-model="packageData.materials.markdown" type="textarea" :rows="12" readonly />
    </section>
  </div>
</template>
```

Use this `<script setup>`:

```ts
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight, CopyDocument, Download, Refresh } from '@element-plus/icons-vue'
import { getTrialDeliveryPackage } from '@/api/dashboard'
import type {
  TrialDeliveryPackage,
  TrialReadinessItemStatus,
  TrialRunbookRecordStatus
} from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const packageData = ref<TrialDeliveryPackage>({
  status: 'action_required',
  generated_at: '',
  summary: {
    readiness_ok: 0,
    readiness_warning: 0,
    readiness_error: 0,
    runbook_checked: 0,
    runbook_blocked: 0,
    runbook_skipped: 0
  },
  audience_sections: [],
  acceptance_checklist: [],
  demo_script: [],
  accounts: [],
  materials: {
    markdown: '',
    json: ''
  }
})

const packageStatusTag = computed(() => packageData.value.status === 'ready' ? 'success' : 'danger')
const summaryCards = computed(() => [
  { label: '正常项', value: packageData.value.summary.readiness_ok, hint: 'readiness ok' },
  { label: '提醒项', value: packageData.value.summary.readiness_warning, hint: 'readiness warning' },
  { label: '阻断项', value: packageData.value.summary.readiness_error, hint: 'readiness error' },
  { label: '演练已检查', value: packageData.value.summary.runbook_checked, hint: 'checked records' },
  { label: '演练阻断', value: packageData.value.summary.runbook_blocked, hint: 'blocked records' },
  { label: '演练跳过', value: packageData.value.summary.runbook_skipped, hint: 'skipped records' }
])

function statusTag(status: TrialReadinessItemStatus) {
  return status === 'ok' ? 'success' : status === 'warning' ? 'warning' : 'danger'
}

function statusText(status: TrialReadinessItemStatus) {
  return status === 'ok' ? '正常' : status === 'warning' ? '提醒' : '阻断'
}

function recordTag(status: TrialRunbookRecordStatus) {
  return status === 'checked' ? 'success' : status === 'blocked' ? 'danger' : 'info'
}

function recordText(status: TrialRunbookRecordStatus) {
  return status === 'checked' ? '已检查' : status === 'blocked' ? '有阻断' : '已跳过'
}

function go(path: string) {
  router.push(path)
}

function downloadText(filename: string, text: string, type: string) {
  const blob = new Blob([text], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function copyMarkdown() {
  try {
    await navigator.clipboard.writeText(packageData.value.materials.markdown)
    ElMessage.success('交付材料已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

function downloadMarkdown() {
  downloadText('trial-delivery-package.md', packageData.value.materials.markdown, 'text/markdown;charset=utf-8')
}

function downloadJson() {
  downloadText('trial-delivery-package.json', packageData.value.materials.json, 'application/json;charset=utf-8')
}

async function loadPackage() {
  loading.value = true
  try {
    const res = await getTrialDeliveryPackage()
    packageData.value = res.data
  } catch (e: any) {
    ElMessage.error(e?.message || '试点交付包加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadPackage)
</script>
```

Use this scoped CSS:

```css
<style scoped>
.trial-delivery-page {
  display: grid;
  gap: 18px;
}

.header-band,
.delivery-section,
.summary-card {
  border: 1px solid #dce7f5;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(20, 60, 120, 0.06);
}

.header-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
}

.header-band h1,
.section-head h2 {
  margin: 0;
  color: #152b4a;
}

.header-band p,
.muted,
.script-list p,
.account-item p,
.account-item em {
  margin: 4px 0 0;
  color: #5f7391;
}

.eyebrow {
  margin: 0 0 6px;
  color: #1f6feb;
  font-size: 12px;
  font-weight: 700;
}

.header-actions,
.material-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  display: grid;
  gap: 6px;
  padding: 16px;
}

.summary-card span,
.summary-card em {
  color: #60728a;
  font-size: 13px;
}

.summary-card strong {
  color: #152b4a;
  font-size: 28px;
}

.delivery-section {
  padding: 18px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.evidence-list,
.account-list {
  display: grid;
  gap: 8px;
}

.evidence-list span {
  display: block;
  color: #344966;
}

.record-note {
  display: grid;
  gap: 6px;
}

.record-note p {
  margin: 0;
  color: #344966;
}

.delivery-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
}

.script-list {
  display: grid;
  gap: 12px;
  margin: 0;
  padding-left: 20px;
}

.script-list li {
  padding-left: 4px;
}

.script-list span,
.account-item span {
  display: block;
  margin-top: 4px;
  color: #1f6feb;
  font-size: 13px;
}

.account-item {
  padding: 12px;
  border: 1px solid #e3ebf6;
  border-radius: 8px;
  background: #f8fbff;
}

.account-item strong {
  color: #152b4a;
}

@media (max-width: 1100px) {
  .summary-grid,
  .delivery-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 760px) {
  .header-band,
  .section-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-grid,
  .delivery-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 5: Update route smoke script**

In `scripts/check_frontend_route_smoke.py`, add this expectation after the admin dashboard expectation:

```python
    RouteExpectation("path: 'trial-delivery'", "views/admin/TrialDeliveryPackage.vue", "试点交付包", ("试点交付包", "现场验收清单", "演示脚本", "测试账号交付", "下载 Markdown", "下载 JSON", "复制交付材料")),
```

- [ ] **Step 6: Run frontend static tests and build**

Run:

```powershell
python -m pytest backend/tests/test_trial_delivery_page.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
Set-Location frontend; npm run build; Set-Location ..
```

Expected: targeted frontend tests pass, route smoke count increases by one, and the frontend build exits 0. Existing Vite/Sass warnings are acceptable if there are no errors.

- [ ] **Step 7: Commit frontend implementation**

Run:

```powershell
git add frontend/src/api/dashboard.ts frontend/src/router/routes.ts frontend/src/layouts/RoleMenu.vue frontend/src/views/admin/TrialDeliveryPackage.vue scripts/check_frontend_route_smoke.py backend/tests/test_trial_delivery_page.py
git commit -m "Add trial delivery package page"
git push
```

- [ ] **Step 8: Update progress after Task 4**

Add a completed-work entry to `docs/superpowers/progress/2026-05-25-platform-progress.md` summarizing the frontend page and targeted verification output.

Run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Record trial delivery frontend page"
git push
```

---

## Task 5: Release Verification And Browser Smoke

**Files:**

- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`

- [ ] **Step 1: Run full release verification**

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-release.ps1
```

Expected: backend tests, backend compile, frontend text health, route smoke, and frontend build pass. Record the backend test count and route smoke count.

- [ ] **Step 2: Restart local services if needed**

If the browser or API is still serving old code, restart local services with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Expected: backend is reachable at `http://127.0.0.1:8000` and frontend is reachable at `http://127.0.0.1:3000`.

- [ ] **Step 3: Browser-smoke `/admin/trial-delivery`**

Use the in-app browser:

1. Log in as `admin` / local default admin password if the session is not authenticated.
2. Open `http://127.0.0.1:3000/admin/trial-delivery`.
3. Confirm the page renders:
   - `试点交付包`
   - `现场验收清单`
   - `演示脚本`
   - `测试账号交付`
   - `复制交付材料`
   - `下载 Markdown`
   - `下载 JSON`
4. Click `复制交付材料` and confirm a success or readable fallback message.
5. Click `下载 Markdown` and `下载 JSON`; if the browser blocks download inspection, confirm no console error is emitted by the click handlers.
6. Confirm browser console has no errors or warnings caused by this page.

- [ ] **Step 4: Update progress and close P12 Batch 1**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

- Mark these P12 items complete:
  - `Write P12 Batch 1 implementation plan.`
  - `Add backend delivery package contract and tests.`
  - `Add read-only delivery package aggregation endpoint.`
  - `Add admin delivery package page and download actions.`
  - `Run release verification, browser smoke, commit, and push.`
- Add a completed-work entry with the release check output and browser-smoke result.
- Keep Phase 12 parent unchecked unless Batch 2 is also completed or explicitly deferred.
- Add a note that P13 will address teacher menu reachable-page gaps after P12.

Run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md
git commit -m "Verify trial delivery package"
git push
```

---

## Self-Review Checklist

- Spec coverage: This plan covers the P12 Batch 1 endpoint, package shape, admin role access, evidence sources, safe account handout wording, dedicated route, page rendering, Markdown/JSON downloads, route smoke, release verification, browser smoke, progress updates, commits, and pushes.
- Scope control: This plan excludes signatures, uploads, PDFs, Provider rehearsal triggers, mutable acceptance state, and P13 teacher menu cleanup.
- Type consistency: Backend names use `get_trial_delivery_package`; frontend names use `TrialDeliveryPackage`, `TrialDeliveryChecklistItem`, `TrialDeliveryDemoStep`, `TrialDeliveryAccount`, and `getTrialDeliveryPackage`.
- Review gate: After this plan is committed and pushed, the user reviews it before implementation starts.
