# Trial Operations Runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dashboard-centered trial operations runbook that groups existing readiness evidence into ordered rehearsal stages for administrators.

**Architecture:** Reuse the existing `DashboardService.get_trial_readiness()` contract as the source of truth, then add a small mapping layer that converts readiness items into six operational stages. Expose the stages through a read-only admin API and render them on the existing Admin Dashboard beside the readiness checklist. The runbook never calls upstream AI providers, mutates trial setup data, or exposes secrets.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, pytest with FastAPI `TestClient`, Vue 3, TypeScript, Element Plus, existing route smoke and release scripts.

---

## File Structure

- Create `backend/tests/test_trial_operations_runbook.py`: backend TDD coverage for the new runbook API, role blocking, stage shape, required keys, and AI-provider route selection.
- Modify `backend/app/services/dashboard_service.py`: add `get_trial_operations_runbook()`, stage mapping helpers, status severity merge, and evidence text generation.
- Modify `backend/app/api/routers/dashboard.py`: add `GET /dashboard/trial-operations/runbook` with the same admin-role gate as `/dashboard/trial-readiness`.
- Modify `frontend/src/api/dashboard.ts`: add runbook TypeScript types and `getTrialOperationsRunbook()`.
- Modify `frontend/src/views/admin/AdminDashboard.vue`: load and render the "试运行演练台" stage panel while preserving the current readiness checklist.
- Create `backend/tests/test_admin_dashboard_trial_ops.py`: static frontend contract coverage for dashboard anchors and API usage.
- Modify `scripts/check_frontend_route_smoke.py`: protect the Admin Dashboard runbook anchors in route smoke.
- Modify `docs/superpowers/progress/2026-05-25-platform-progress.md`: update P11 progress after every stage.
- Modify `docs/superpowers/plans/2026-05-28-trial-operations-runbook.md`: check off tasks and record observed command output as work completes.

---

### Task 1: Backend Red Tests for Runbook Contract

**Files:**
- Create: `backend/tests/test_trial_operations_runbook.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-operations-runbook.md`

- [ ] **Step 1: Write the failing API tests**

Create `backend/tests/test_trial_operations_runbook.py` with this initial content:

```python
import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.seed import ADMIN_ID, SCHOOL_ID
from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.ai_agent_call import AIAgentCall


def _login(client: TestClient, username: str) -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _stage_map(data: dict) -> dict[str, dict]:
    return {stage["key"]: stage for stage in data["stages"]}


def test_system_admin_can_view_trial_operations_runbook():
    with TestClient(app) as client:
        headers = _login(client, "admin")

        response = client.get(
            "/api/v1/dashboard/trial-operations/runbook",
            headers=headers,
        )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] in {"ready", "action_required"}
    assert isinstance(data["checked_at"], str)
    assert set(data["summary"].keys()) == {"ok", "warning", "error"}

    stages = data["stages"]
    assert [stage["key"] for stage in stages] == [
        "service_readiness",
        "base_data",
        "account_access",
        "ai_provider_rehearsal",
        "teaching_workflow",
        "resource_and_backup",
    ]

    for stage in stages:
        assert set(stage.keys()) == {
            "key",
            "title",
            "status",
            "owner",
            "route",
            "primary_action",
            "evidence",
            "next_step",
        }
        assert stage["status"] in {"ok", "warning", "error"}
        assert stage["title"]
        assert stage["owner"]
        assert stage["route"].startswith("/")
        assert stage["primary_action"]
        assert isinstance(stage["evidence"], list)
        assert stage["evidence"]
        assert stage["next_step"]


def test_school_admin_can_view_trial_operations_runbook_and_teacher_is_blocked():
    with TestClient(app) as client:
        school_admin_headers = _login(client, "schooladmin")
        teacher_headers = _login(client, "teacher001")

        school_admin_response = client.get(
            "/api/v1/dashboard/trial-operations/runbook",
            headers=school_admin_headers,
        )
        teacher_response = client.get(
            "/api/v1/dashboard/trial-operations/runbook",
            headers=teacher_headers,
        )

    assert school_admin_response.status_code == 200, school_admin_response.text
    assert len(school_admin_response.json()["data"]["stages"]) == 6
    assert teacher_response.status_code == 403
    assert teacher_response.json()["code"] == 403001


def test_ai_provider_stage_links_to_ai_call_diagnostics_when_recent_real_provider_failed():
    async def seed_failed_real_provider_call():
        async with AsyncSessionFactory() as session:
            existing = await session.execute(
                select(AIAgentCall).where(AIAgentCall.id == "runbook-failed-call-0001")
            )
            call = existing.scalar_one_or_none()
            if call is None:
                call = AIAgentCall(
                    id="runbook-failed-call-0001",
                    agent_id="agent-lesson-plan-0000-0000-0001",
                    user_id=ADMIN_ID,
                    school_id=SCHOOL_ID,
                    scenario="lesson_plan",
                    provider="qwen_agent",
                    status="failed",
                    review_status="pending",
                    request_payload={"theme": "runbook diagnostics"},
                    response_payload={},
                    diagnostic_metadata={
                        "error_category": "configuration_missing",
                        "provider": "qwen_agent",
                        "retryable": False,
                        "safe_metadata": {"missing": ["endpoint"]},
                    },
                    error_message="Provider configuration is incomplete",
                )
                session.add(call)
            await session.commit()

    asyncio.run(seed_failed_real_provider_call())

    with TestClient(app) as client:
        headers = _login(client, "admin")
        response = client.get(
            "/api/v1/dashboard/trial-operations/runbook",
            headers=headers,
        )

    assert response.status_code == 200, response.text
    ai_stage = _stage_map(response.json()["data"])["ai_provider_rehearsal"]
    assert ai_stage["status"] in {"warning", "error"}
    assert ai_stage["route"] in {"/admin/ai-calls", "/admin/ai-agents"}
    assert any("AI" in evidence or "Provider" in evidence for evidence in ai_stage["evidence"])
    assert "Provider" in ai_stage["title"]
```

- [ ] **Step 2: Run the new test to confirm the red state**

Run:

```powershell
python -m pytest backend/tests/test_trial_operations_runbook.py -q
```

Expected: fail with 404 for `/api/v1/dashboard/trial-operations/runbook` because the route is not implemented yet.

- [ ] **Step 3: Update progress and commit the red tests**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Started P11 Batch 1 Task 1 backend TDD. Added failing `backend/tests/test_trial_operations_runbook.py` coverage for admin access, teacher blocking, required six runbook stages, stage response shape, and AI Provider diagnostics route selection. Verified red state with `python -m pytest backend/tests/test_trial_operations_runbook.py -q` failing because `/api/v1/dashboard/trial-operations/runbook` is not implemented yet.
```

Mark this task's checkboxes in the plan. Then run:

```powershell
git add backend/tests/test_trial_operations_runbook.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-operations-runbook.md
git commit -m "Add trial operations runbook red tests"
git push
```

Expected: commit and push succeed. If push fails due transient network reset, inspect `git status --short --branch` and retry once before escalating.

---

### Task 2: Backend Runbook Endpoint

**Files:**
- Modify: `backend/app/services/dashboard_service.py`
- Modify: `backend/app/api/routers/dashboard.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-operations-runbook.md`

- [ ] **Step 1: Add the route**

In `backend/app/api/routers/dashboard.py`, add this route immediately after `get_trial_readiness`:

```python
@router.get("/trial-operations/runbook")
async def get_trial_operations_runbook(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Get the stage-by-stage operations runbook for local trial rehearsal."""
    data = await DashboardService.get_trial_operations_runbook(db=db)
    return success_response(data=data, message="试运行演练台已生成")
```

- [ ] **Step 2: Add runbook service helpers**

In `backend/app/services/dashboard_service.py`, add `get_trial_operations_runbook()` after `get_trial_readiness()`:

```python
    @staticmethod
    async def get_trial_operations_runbook(db: AsyncSession) -> dict:
        """Return ordered trial rehearsal stages derived from readiness evidence."""
        readiness = await DashboardService.get_trial_readiness(db)
        items = {item["key"]: item for item in readiness["items"]}
        stages = [
            DashboardService._runbook_stage(
                key="service_readiness",
                title="服务与数据可用",
                owner="平台管理员",
                items=[items.get("service_readiness")],
                route="/admin",
                primary_action="查看 readiness",
                next_step="确认本地服务、数据库和上传目录可用后，进入基础数据检查。",
            ),
            DashboardService._runbook_stage(
                key="base_data",
                title="基础数据演练",
                owner="区县/学校管理员",
                items=[items.get("organization_data")],
                route="/admin/schools",
                primary_action="核对学校班级学科",
                next_step="学校、班级和学科齐备后，继续核对试点账号。",
            ),
            DashboardService._runbook_stage(
                key="account_access",
                title="账号登录演练",
                owner="学校管理员",
                items=[items.get("user_accounts")],
                route="/admin/users",
                primary_action="核对教师学生账号",
                next_step="确认教师和学生账号可以登录，并准备初始密码发放清单。",
            ),
            DashboardService._ai_provider_runbook_stage(items.get("ai_contract")),
            DashboardService._runbook_stage(
                key="teaching_workflow",
                title="教学闭环演练",
                owner="试点教师",
                items=[items.get("teaching_workflow"), items.get("student_task_availability")],
                route="/teacher/projects",
                primary_action="演练项目到任务闭环",
                next_step="确认教师可创建或采纳项目，学生端可看到已发布任务。",
            ),
            DashboardService._resource_backup_runbook_stage(
                items.get("resources"),
                items.get("backup_path"),
            ),
        ]
        summary = {
            "ok": sum(1 for stage in stages if stage["status"] == "ok"),
            "warning": sum(1 for stage in stages if stage["status"] == "warning"),
            "error": sum(1 for stage in stages if stage["status"] == "error"),
        }
        return {
            "status": "action_required" if summary["error"] else "ready",
            "checked_at": readiness["checked_at"],
            "summary": summary,
            "stages": stages,
        }
```

Add helper methods near `_item()`:

```python
    @staticmethod
    def _runbook_stage(
        key: str,
        title: str,
        owner: str,
        items: list[Optional[dict]],
        route: str,
        primary_action: str,
        next_step: str,
    ) -> dict:
        present_items = [item for item in items if item]
        return {
            "key": key,
            "title": title,
            "status": DashboardService._worst_status(present_items),
            "owner": owner,
            "route": route,
            "primary_action": primary_action,
            "evidence": DashboardService._stage_evidence(present_items),
            "next_step": next_step,
        }

    @staticmethod
    def _worst_status(items: list[dict]) -> str:
        order = {"ok": 0, "warning": 1, "error": 2}
        if not items:
            return "warning"
        return max((item["status"] for item in items), key=lambda status: order.get(status, 1))

    @staticmethod
    def _stage_evidence(items: list[dict]) -> list[str]:
        if not items:
            return ["暂无 readiness 证据"]
        return [
            f"{item['label']}：{item['metric']}（{DashboardService._status_label(item['status'])}）"
            for item in items
        ]

    @staticmethod
    def _status_label(status: str) -> str:
        if status == "ok":
            return "正常"
        if status == "warning":
            return "提醒"
        return "阻断"
```

Add AI/resource specialized helpers after `_stage_evidence()`:

```python
    @staticmethod
    def _ai_provider_runbook_stage(ai_item: Optional[dict]) -> dict:
        route = "/admin/ai-agents"
        action = "执行 Provider 配置自检"
        next_step = "保持 mock/manual 可演练；真实 Provider 接入前先完成配置自检，再查看失败诊断。"
        if ai_item and ai_item.get("route") == "/admin/ai-calls":
            route = "/admin/ai-calls"
            action = "查看 AI 调用诊断"
            next_step = "先处理近期真实 Provider 调用失败，再继续教师侧生成演练。"
        return DashboardService._runbook_stage(
            key="ai_provider_rehearsal",
            title="AI Provider演练",
            owner="平台管理员",
            items=[ai_item],
            route=route,
            primary_action=action,
            next_step=next_step,
        )

    @staticmethod
    def _resource_backup_runbook_stage(resource_item: Optional[dict], backup_item: Optional[dict]) -> dict:
        status = DashboardService._worst_status([item for item in [resource_item, backup_item] if item])
        route = "/teacher/resources" if resource_item and resource_item.get("status") != "ok" else "/admin"
        action = "补齐资源或执行备份"
        if backup_item and backup_item.get("status") != "ok":
            route = "/admin"
            action = "核对备份路径"
        return DashboardService._runbook_stage(
            key="resource_and_backup",
            title="资源与备份演练",
            owner="平台管理员",
            items=[resource_item, backup_item],
            route=route,
            primary_action=action,
            next_step="确认演示资源可用，并在正式试运行前完成一次 SQLite 备份演练。",
        ) | {"status": status}
```

- [ ] **Step 3: Run targeted backend tests**

Run:

```powershell
python -m pytest backend/tests/test_trial_operations_runbook.py backend/tests/test_trial_readiness.py backend/tests/test_ai_call_failure_observability.py::test_trial_readiness_warns_when_recent_real_provider_failure_exists -q
```

Expected: all selected tests pass.

- [ ] **Step 4: Compile backend**

Run:

```powershell
python -m compileall backend\app
```

Expected: compile succeeds.

- [ ] **Step 5: Update progress and commit backend implementation**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Completed P11 Batch 1 backend runbook endpoint. Added `GET /api/v1/dashboard/trial-operations/runbook`, derived six ordered rehearsal stages from existing readiness evidence, preserved admin-only access, and routed the AI Provider stage to `/admin/ai-agents` or `/admin/ai-calls` according to current risk. Verified with `python -m pytest backend/tests/test_trial_operations_runbook.py backend/tests/test_trial_readiness.py backend/tests/test_ai_call_failure_observability.py::test_trial_readiness_warns_when_recent_real_provider_failure_exists -q` and `python -m compileall backend\app`.
```

Mark this task's checkboxes in the plan. Then run:

```powershell
git add backend/app/services/dashboard_service.py backend/app/api/routers/dashboard.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-operations-runbook.md
git commit -m "Add trial operations runbook endpoint"
git push
```

Expected: commit and push succeed.

---

### Task 3: Frontend Dashboard Runbook Panel

**Files:**
- Modify: `frontend/src/api/dashboard.ts`
- Modify: `frontend/src/views/admin/AdminDashboard.vue`
- Create: `backend/tests/test_admin_dashboard_trial_ops.py`
- Modify: `scripts/check_frontend_route_smoke.py`
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-operations-runbook.md`

- [ ] **Step 1: Write the failing frontend static test**

Create `backend/tests/test_admin_dashboard_trial_ops.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "views" / "admin" / "AdminDashboard.vue"
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_admin_dashboard_renders_trial_operations_runbook_panel():
    text = PAGE.read_text(encoding="utf-8")

    for label in [
        "试运行演练台",
        "演练阶段",
        "责任角色",
        "证据",
        "下一步",
        "Provider演练",
        "getTrialOperationsRunbook",
        "trialRunbook",
    ]:
        assert label in text


def test_dashboard_api_exposes_trial_operations_runbook_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TrialOperationsRunbook",
        "TrialOperationsStage",
        "getTrialOperationsRunbook",
        "/dashboard/trial-operations/runbook",
    ]:
        assert label in text


def test_route_smoke_protects_trial_operations_runbook_anchors():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in ["试运行演练台", "演练阶段", "Provider演练"]:
        assert label in text
```

Run:

```powershell
python -m pytest backend/tests/test_admin_dashboard_trial_ops.py -q
```

Expected: fail because API types, dashboard anchors, and route smoke anchors are not implemented yet.

- [ ] **Step 2: Add API types and request**

In `frontend/src/api/dashboard.ts`, add these interfaces after `TrialReadiness`:

```ts
export interface TrialOperationsStage {
  key: string
  title: string
  status: TrialReadinessItemStatus
  owner: string
  route: string
  primary_action: string
  evidence: string[]
  next_step: string
}

export interface TrialOperationsRunbook {
  status: TrialReadinessStatus
  checked_at: string
  summary: {
    ok: number
    warning: number
    error: number
  }
  stages: TrialOperationsStage[]
}
```

Add the request function after `getTrialReadiness()`:

```ts
export function getTrialOperationsRunbook(): Promise<ApiResponse<TrialOperationsRunbook>> {
  return request.get('/dashboard/trial-operations/runbook')
}
```

- [ ] **Step 3: Render the runbook panel**

In `frontend/src/views/admin/AdminDashboard.vue`:

1. Import `getTrialOperationsRunbook`, `TrialOperationsRunbook`, and `TrialOperationsStage`.
2. Add state:

```ts
const trialRunbook = ref<TrialOperationsRunbook>({
  status: 'action_required',
  checked_at: '',
  summary: { ok: 0, warning: 0, error: 0 },
  stages: []
})
```

3. Update `loadData()` to request the runbook:

```ts
const [overviewRes, trendsRes, aiRes, readinessRes, runbookRes] = await Promise.all([
  getDashboardOverview(),
  getProjectTrends(),
  getAIUsage(),
  getTrialReadiness(),
  getTrialOperationsRunbook()
])
trialRunbook.value = runbookRes.data
```

4. Add a new section after the readiness panel:

```vue
<section class="runbook-panel">
  <div class="runbook-head">
    <div>
      <p class="eyebrow">试运行演练台</p>
      <h2>演练阶段</h2>
      <p>按运营顺序串联 readiness 证据、责任角色和下一步处理入口。</p>
    </div>
    <div class="readiness-summary">
      <el-tag :type="runbookTagType" effect="dark">
        {{ trialRunbook.status === 'ready' ? '演练可继续' : '需要处理' }}
      </el-tag>
      <span>正常 {{ trialRunbook.summary.ok }}</span>
      <span>提醒 {{ trialRunbook.summary.warning }}</span>
      <span>阻断 {{ trialRunbook.summary.error }}</span>
    </div>
  </div>

  <div class="runbook-list">
    <article v-for="stage in trialRunbook.stages" :key="stage.key" class="runbook-stage">
      <div class="stage-top">
        <el-tag :type="itemTagType(stage.status)" effect="light">
          {{ itemStatusText(stage.status) }}
        </el-tag>
        <h3>{{ stage.title }}</h3>
      </div>
      <dl>
        <div>
          <dt>责任角色</dt>
          <dd>{{ stage.owner }}</dd>
        </div>
        <div>
          <dt>证据</dt>
          <dd>
            <span v-for="evidence in stage.evidence" :key="evidence">{{ evidence }}</span>
          </dd>
        </div>
        <div>
          <dt>下一步</dt>
          <dd>{{ stage.next_step }}</dd>
        </div>
      </dl>
      <el-button text type="primary" :icon="ArrowRight" @click="goTo(stage.route)">
        {{ stage.primary_action }}
      </el-button>
    </article>
  </div>
</section>
```

5. Add computed tag type:

```ts
const runbookTagType = computed(() => (
  trialRunbook.value.status === 'ready' ? 'success' : 'danger'
))
```

6. Add CSS classes with stable compact layout:

```css
.runbook-panel {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  padding: 18px;
}

.runbook-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.runbook-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.runbook-stage {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 14px;
  display: grid;
  gap: 10px;
}

.stage-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-top h3 {
  margin: 0;
  color: #1f2f5f;
  font-size: 15px;
}

.runbook-stage dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

.runbook-stage dt {
  color: #6b7280;
  font-size: 12px;
}

.runbook-stage dd {
  margin: 2px 0 0;
  color: #303133;
  font-size: 13px;
}

.runbook-stage dd span {
  display: block;
  line-height: 1.5;
}
```

Add mobile rule beside the existing media block:

```css
.runbook-head {
  flex-direction: column;
}
```

- [ ] **Step 4: Update route smoke anchors**

In `scripts/check_frontend_route_smoke.py`, change the Admin Dashboard expectation anchors from:

```python
("管理驾驶舱", "试运行检查清单")
```

to:

```python
("管理驾驶舱", "试运行检查清单", "试运行演练台", "演练阶段", "Provider演练")
```

- [ ] **Step 5: Run frontend targeted checks**

Run:

```powershell
python -m pytest backend/tests/test_admin_dashboard_trial_ops.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
npm run build
```

Expected: all tests pass and frontend build succeeds.

- [ ] **Step 6: Update progress and commit frontend implementation**

Update `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- 2026-05-28: Completed P11 Batch 1 admin dashboard runbook UI. Added dashboard API types, loaded `getTrialOperationsRunbook()`, rendered the `试运行演练台` with stage status, responsibility, evidence, next step, and route actions, and protected the new anchors with static tests and route smoke. Verified with `python -m pytest backend/tests/test_admin_dashboard_trial_ops.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q` and `npm run build`.
```

Mark this task's checkboxes in the plan. Then run:

```powershell
git add frontend/src/api/dashboard.ts frontend/src/views/admin/AdminDashboard.vue backend/tests/test_admin_dashboard_trial_ops.py scripts/check_frontend_route_smoke.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-operations-runbook.md
git commit -m "Add admin trial operations runbook UI"
git push
```

Expected: commit and push succeed.

---

### Task 4: Release Verification and Browser Smoke

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-28-trial-operations-runbook.md`

- [ ] **Step 1: Run the full release check**

Run:

```powershell
scripts/check-release.ps1
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

Verify visible anchors:

- `管理驾驶舱`
- `试运行检查清单`
- `试运行演练台`
- `演练阶段`
- `Provider演练`
- `责任角色`
- `证据`
- `下一步`

Also verify the browser console has no new errors or warnings.

- [ ] **Step 3: Update progress and complete P11 Batch 1**

Update the Phase 11 checklist in `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- [x] Add backend runbook contract and tests.
- [x] Add admin dashboard runbook UI.
- [x] Run release verification, browser smoke, commit, and push.
```

Add a completed-work entry:

```markdown
- 2026-05-28: Completed P11 Batch 1 verification and smoke. `scripts/check-release.ps1` passed with backend tests, backend compile, frontend text health, route smoke, and frontend build. Browser smoke confirmed `/admin` renders the readiness checklist and `试运行演练台` stage panel with Provider rehearsal, responsibility, evidence, and next-step labels without console errors.
```

Mark this task's checkboxes in the plan. Then run:

```powershell
git add docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-28-trial-operations-runbook.md
git commit -m "Verify trial operations runbook"
git push
```

Expected: commit and push succeed.

---

## Self-Review

- Spec coverage: the plan covers the new read-only runbook endpoint, six required stage keys, admin role gate, AI Provider route selection, dashboard UI, static anchors, route smoke, release verification, browser smoke, progress updates, and push after each stage.
- Placeholder scan: no draft markers remain; each task has exact files, commands, and expected outcomes.
- Type consistency: backend uses `stages`, `primary_action`, `next_step`, and `evidence`; frontend `TrialOperationsStage` uses the same field names.
- Scope check: P11 Batch 1 stays dashboard-centered and does not add a new route, historical rehearsal logs, upstream Provider calls, or mutating rehearsal actions.
