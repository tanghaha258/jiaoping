# Teacher-Side Core Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete P13 Batch 1 by turning the teacher side into a real workflow hub with deterministic learning diagnosis, classroom implementation, and teaching improvement pages.

**Architecture:** Add one teacher-scoped dashboard aggregation endpoint and reuse it across the teacher dashboard plus three new teacher pages. Keep the implementation deterministic and local-data-backed: no AI calls, no new domain tables, and no mutable classroom/live-session state.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, existing `DashboardService`, Vue 3, Element Plus, Pinia auth store, static pytest route/text checks, release verification.

---

## Scope Guard

Included:

- `GET /api/v1/dashboard/teacher/workflow-summary` for teacher-scoped workflow data.
- Teacher dashboard rewrite around next actions and teaching-loop status.
- New teacher pages:
  - `/teacher/diagnosis` -> `LearningDiagnosis.vue`
  - `/teacher/classroom` -> `ClassroomImplementation.vue`
  - `/teacher/improvements` -> `TeachingImprovements.vue`
- Teacher menu route cleanup so every visible teacher menu item navigates to a real page.
- Frontend API types/helper for the workflow summary.
- Static route smoke anchors and browser smoke.
- Progress doc update, release verification, commit, and push.

Excluded:

- Resource subroutes from P13 Batch 2.
- Real-time classroom interaction, attendance, live polling, websocket state, or screen broadcasting.
- AI-generated improvement suggestions.
- New question-bank/case-library CRUD.
- New school-admin or region-admin powers in the teacher role.

## Files

- Create: `backend/tests/test_teacher_workflow_summary.py`
  - Backend TDD for the teacher workflow summary endpoint, role blocking, empty-state safety, and deterministic blocks.
- Create: `backend/tests/test_teacher_page_completion.py`
  - Static frontend contract tests for dashboard API types, routes, menu entries, and new page anchors.
- Modify: `backend/app/api/routers/dashboard.py`
  - Add `/dashboard/teacher/workflow-summary` protected by `require_roles("teacher")`.
- Modify: `backend/app/services/dashboard_service.py`
  - Add `get_teacher_workflow_summary(db, teacher)` and small private helpers as needed.
- Modify: `frontend/src/api/dashboard.ts`
  - Add TypeScript interfaces and `getTeacherWorkflowSummary()`.
- Modify: `frontend/src/router/routes.ts`
  - Add teacher child routes for `diagnosis`, `classroom`, and `improvements`.
- Modify: `frontend/src/layouts/RoleMenu.vue`
  - Route teacher menu entries to real pages and remove misleading school/region admin entries from the teacher role.
- Modify: `frontend/src/views/teacher/TeacherDashboard.vue`
  - Rework as a compact teacher workflow hub backed by workflow summary.
- Create: `frontend/src/views/teacher/LearningDiagnosis.vue`
- Create: `frontend/src/views/teacher/ClassroomImplementation.vue`
- Create: `frontend/src/views/teacher/TeachingImprovements.vue`
- Modify: `scripts/check_frontend_route_smoke.py`
  - Protect the new routes and visible anchors.
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
  - Track P13 Batch 1 start/completion after verification.

## Data Contract

Use this stable response shape for the backend endpoint and frontend types:

```json
{
  "overview": {
    "active_projects": 0,
    "draft_tasks": 0,
    "published_tasks": 0,
    "pending_submissions": 0,
    "draft_evaluations": 0,
    "confirmed_evaluations": 0,
    "available_resources": 0
  },
  "next_actions": [
    {
      "key": "review_submissions",
      "title": "处理待审阅提交",
      "count": 0,
      "route": "/teacher/evaluations",
      "priority": "high"
    }
  ],
  "diagnosis": {
    "class_signals": [
      {
        "key": "pending_submissions",
        "title": "待跟进提交",
        "value": 0,
        "description": "已提交但尚未形成教师评价的作品数量。",
        "route": "/teacher/evaluations"
      }
    ],
    "task_completion": [
      {
        "task_id": "task-id",
        "task_title": "任务标题",
        "project_name": "项目名称",
        "status": "published",
        "submission_count": 0,
        "route": "/teacher/tasks/task-id/submissions"
      }
    ],
    "rubric_signals": [
      {
        "dimension": "科学探究",
        "average_score": 3.0,
        "max_score": 5.0,
        "level": "attention",
        "description": "该维度近期得分偏低，建议补充示例或调整任务说明。"
      }
    ]
  },
  "classroom": {
    "active_task_cards": [
      {
        "task_id": "task-id",
        "task_title": "任务标题",
        "project_id": "project-id",
        "project_name": "项目名称",
        "task_type": "group",
        "due_at": null,
        "submission_count": 0,
        "review_route": "/teacher/tasks/task-id/submissions",
        "project_route": "/teacher/projects/project-id"
      }
    ]
  },
  "improvements": {
    "suggestions": [
      {
        "key": "finish_feedback_loop",
        "title": "先完成反馈闭环",
        "description": "有提交尚未形成教师评价，建议先处理评价反馈。",
        "route": "/teacher/evaluations",
        "priority": "high"
      }
    ]
  }
}
```

For empty datasets, return all blocks with zero counts and at least one low-priority suggestion that guides the teacher to create or activate a project.

## Task 1: Backend Contract Tests

**Files:**

- Create: `backend/tests/test_teacher_workflow_summary.py`

- [ ] **Step 1: Add failing teacher workflow summary tests**

Create `backend/tests/test_teacher_workflow_summary.py` with:

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
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_teacher_can_view_workflow_summary():
    with TestClient(app) as client:
        headers = _login(client, "teacher001")
        response = client.get(
            "/api/v1/dashboard/teacher/workflow-summary",
            headers=headers,
        )

    assert response.status_code == 200, response.text
    summary = response.json()["data"]

    assert set(summary) == {"overview", "next_actions", "diagnosis", "classroom", "improvements"}
    assert set(summary["overview"]) == {
        "active_projects",
        "draft_tasks",
        "published_tasks",
        "pending_submissions",
        "draft_evaluations",
        "confirmed_evaluations",
        "available_resources",
    }
    assert isinstance(summary["next_actions"], list)
    assert isinstance(summary["diagnosis"]["class_signals"], list)
    assert isinstance(summary["diagnosis"]["task_completion"], list)
    assert isinstance(summary["diagnosis"]["rubric_signals"], list)
    assert isinstance(summary["classroom"]["active_task_cards"], list)
    assert isinstance(summary["improvements"]["suggestions"], list)
    assert any(action["route"].startswith("/teacher") for action in summary["next_actions"])


def test_workflow_summary_is_teacher_only():
    with TestClient(app) as client:
        admin_headers = _login(client, "admin")
        student_headers = _login(client, "student001")

        admin_response = client.get(
            "/api/v1/dashboard/teacher/workflow-summary",
            headers=admin_headers,
        )
        student_response = client.get(
            "/api/v1/dashboard/teacher/workflow-summary",
            headers=student_headers,
        )

    assert admin_response.status_code == 403
    assert admin_response.json()["code"] == 403001
    assert student_response.status_code == 403
    assert student_response.json()["code"] == 403001


def test_workflow_summary_contains_safe_empty_state_for_teacher_without_activity():
    with TestClient(app) as client:
        headers = _login(client, "teacher002")
        response = client.get(
            "/api/v1/dashboard/teacher/workflow-summary",
            headers=headers,
        )

    assert response.status_code == 200, response.text
    summary = response.json()["data"]

    assert all(isinstance(value, int) and value >= 0 for value in summary["overview"].values())
    assert summary["next_actions"]
    assert summary["improvements"]["suggestions"]
    assert "password" not in response.text.lower()
    assert "secret" not in response.text.lower()
```

- [ ] **Step 2: Run backend contract tests and confirm red**

Run:

```powershell
python -m pytest backend/tests/test_teacher_workflow_summary.py -q
```

Expected:

- Fails because `/api/v1/dashboard/teacher/workflow-summary` does not exist yet.
- The failure should include `404` or missing route behavior.

## Task 2: Backend Workflow Summary Implementation

**Files:**

- Modify: `backend/app/api/routers/dashboard.py`
- Modify: `backend/app/services/dashboard_service.py`
- Test: `backend/tests/test_teacher_workflow_summary.py`

- [ ] **Step 1: Add dashboard route**

In `backend/app/api/routers/dashboard.py`, add this route near the existing general dashboard endpoints:

```python
@router.get("/teacher/workflow-summary")
async def get_teacher_workflow_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Get deterministic teaching-loop summary data for the current teacher."""
    data = await DashboardService.get_teacher_workflow_summary(db=db, teacher=current_user)
    return success_response(data=data, message="教师工作流概览已生成")
```

- [ ] **Step 2: Add imports needed by aggregation**

In `backend/app/services/dashboard_service.py`, update imports:

```python
from app.models.evaluation import Evaluation
from app.models.submission import Submission
```

Keep existing imports intact.

- [ ] **Step 3: Add workflow summary method**

Add this method inside `DashboardService`:

```python
    @staticmethod
    async def get_teacher_workflow_summary(db: AsyncSession, teacher: User) -> dict:
        """Return deterministic teaching-loop summary data for one teacher."""
        project_ids_result = await db.execute(
            select(Project.id).where(Project.owner_id == teacher.id)
        )
        project_ids = [row[0] for row in project_ids_result.all()]

        active_projects = await DashboardService._count_teacher_projects(db, teacher.id, "active")
        draft_tasks = await DashboardService._count_teacher_tasks(db, teacher.id, "draft")
        published_tasks = await DashboardService._count_teacher_tasks(db, teacher.id, "published")
        pending_submissions = await DashboardService._count_teacher_pending_submissions(db, teacher.id)
        draft_evaluations = await DashboardService._count_teacher_evaluations(db, teacher.id, "draft")
        confirmed_evaluations = await DashboardService._count_teacher_evaluations(db, teacher.id, "confirmed")
        available_resources = await DashboardService._count_teacher_resources(db, teacher.school_id)

        overview = {
            "active_projects": active_projects,
            "draft_tasks": draft_tasks,
            "published_tasks": published_tasks,
            "pending_submissions": pending_submissions,
            "draft_evaluations": draft_evaluations,
            "confirmed_evaluations": confirmed_evaluations,
            "available_resources": available_resources,
        }

        diagnosis = await DashboardService._teacher_diagnosis_block(db, teacher.id)
        classroom = await DashboardService._teacher_classroom_block(db, teacher.id)
        improvements = DashboardService._teacher_improvement_block(overview, diagnosis)
        next_actions = DashboardService._teacher_next_actions(overview)

        return {
            "overview": overview,
            "next_actions": next_actions,
            "diagnosis": diagnosis,
            "classroom": classroom,
            "improvements": improvements,
        }
```

- [ ] **Step 4: Add count helpers**

Add these private helpers inside `DashboardService`:

```python
    @staticmethod
    async def _count_teacher_projects(db: AsyncSession, teacher_id: str, status: str) -> int:
        result = await db.execute(
            select(func.count()).select_from(Project).where(
                Project.owner_id == teacher_id,
                Project.status == status,
            )
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def _count_teacher_tasks(db: AsyncSession, teacher_id: str, status: str) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Task)
            .join(Project, Task.project_id == Project.id)
            .where(Project.owner_id == teacher_id, Task.status == status)
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def _count_teacher_pending_submissions(db: AsyncSession, teacher_id: str) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Submission)
            .join(Task, Submission.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .where(Project.owner_id == teacher_id, Submission.status == "submitted")
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def _count_teacher_evaluations(db: AsyncSession, teacher_id: str, status: str) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(Evaluation)
            .where(Evaluation.evaluator_id == teacher_id, Evaluation.status == status)
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def _count_teacher_resources(db: AsyncSession, school_id: Optional[str]) -> int:
        query = select(func.count()).select_from(Resource).where(Resource.status == "approved")
        if school_id:
            query = query.where(
                Resource.visibility.in_(["system", "region", "school", "personal"])
            )
        result = await db.execute(query)
        return int(result.scalar() or 0)
```

- [ ] **Step 5: Add diagnosis/classroom/improvement helpers**

Add these helpers inside `DashboardService`:

```python
    @staticmethod
    async def _teacher_diagnosis_block(db: AsyncSession, teacher_id: str) -> dict:
        task_rows = await db.execute(
            select(Task.id, Task.title, Task.status, Project.name)
            .join(Project, Task.project_id == Project.id)
            .where(Project.owner_id == teacher_id)
            .order_by(Task.updated_at.desc())
            .limit(8)
        )
        task_completion = []
        for task_id, task_title, task_status, project_name in task_rows.all():
            submission_count_result = await db.execute(
                select(func.count()).select_from(Submission).where(Submission.task_id == task_id)
            )
            submission_count = int(submission_count_result.scalar() or 0)
            task_completion.append(
                {
                    "task_id": task_id,
                    "task_title": task_title,
                    "project_name": project_name,
                    "status": task_status,
                    "submission_count": submission_count,
                    "route": f"/teacher/tasks/{task_id}/submissions",
                }
            )

        pending_submissions = await DashboardService._count_teacher_pending_submissions(db, teacher_id)
        class_signals = [
            {
                "key": "pending_submissions",
                "title": "待跟进提交",
                "value": pending_submissions,
                "description": "已提交但尚未形成教师评价的作品数量。",
                "route": "/teacher/evaluations",
            }
        ]

        evaluation_rows = await db.execute(
            select(Evaluation.scores)
            .where(Evaluation.evaluator_id == teacher_id)
            .order_by(Evaluation.updated_at.desc())
            .limit(20)
        )
        dimension_totals: dict[str, list[float]] = {}
        for (scores,) in evaluation_rows.all():
            if not isinstance(scores, dict):
                continue
            for dimension, score in scores.items():
                if isinstance(score, (int, float)):
                    dimension_totals.setdefault(str(dimension), []).append(float(score))

        rubric_signals = []
        for dimension, values in dimension_totals.items():
            average = round(sum(values) / len(values), 1)
            if average <= 3:
                rubric_signals.append(
                    {
                        "dimension": dimension,
                        "average_score": average,
                        "max_score": 5,
                        "level": "attention",
                        "description": "该维度近期得分偏低，建议补充示例或调整任务说明。",
                    }
                )

        return {
            "class_signals": class_signals,
            "task_completion": task_completion,
            "rubric_signals": rubric_signals,
        }

    @staticmethod
    async def _teacher_classroom_block(db: AsyncSession, teacher_id: str) -> dict:
        rows = await db.execute(
            select(Task.id, Task.title, Task.task_type, Task.due_at, Project.id, Project.name)
            .join(Project, Task.project_id == Project.id)
            .where(Project.owner_id == teacher_id, Task.status == "published")
            .order_by(Task.updated_at.desc())
            .limit(8)
        )

        cards = []
        for task_id, title, task_type, due_at, project_id, project_name in rows.all():
            submission_count_result = await db.execute(
                select(func.count()).select_from(Submission).where(Submission.task_id == task_id)
            )
            submission_count = int(submission_count_result.scalar() or 0)
            cards.append(
                {
                    "task_id": task_id,
                    "task_title": title,
                    "project_id": project_id,
                    "project_name": project_name,
                    "task_type": task_type,
                    "due_at": due_at.isoformat() if due_at else None,
                    "submission_count": submission_count,
                    "review_route": f"/teacher/tasks/{task_id}/submissions",
                    "project_route": f"/teacher/projects/{project_id}",
                }
            )
        return {"active_task_cards": cards}

    @staticmethod
    def _teacher_improvement_block(overview: dict, diagnosis: dict) -> dict:
        suggestions = []
        if overview["pending_submissions"] > 0:
            suggestions.append(
                {
                    "key": "finish_feedback_loop",
                    "title": "先完成反馈闭环",
                    "description": f"有 {overview['pending_submissions']} 条提交尚未形成教师评价，建议先处理评价反馈。",
                    "route": "/teacher/evaluations",
                    "priority": "high",
                }
            )
        if diagnosis["rubric_signals"]:
            suggestions.append(
                {
                    "key": "support_low_dimensions",
                    "title": "补强薄弱评价维度",
                    "description": "部分评价维度近期得分偏低，建议补充示例资源或调整下一课任务说明。",
                    "route": "/teacher/resources",
                    "priority": "medium",
                }
            )
        if overview["published_tasks"] == 0:
            suggestions.append(
                {
                    "key": "publish_task",
                    "title": "发布一个学习任务",
                    "description": "当前没有已发布任务，建议从项目详情中发布一条任务完成课堂实施演练。",
                    "route": "/teacher/projects",
                    "priority": "medium",
                }
            )
        if not suggestions:
            suggestions.append(
                {
                    "key": "keep_loop_running",
                    "title": "继续推进教学闭环",
                    "description": "当前核心流程暂无阻断，可继续优化项目任务、资源和评价反馈。",
                    "route": "/teacher/projects",
                    "priority": "low",
                }
            )
        return {"suggestions": suggestions}

    @staticmethod
    def _teacher_next_actions(overview: dict) -> list[dict]:
        actions = []
        if overview["pending_submissions"] > 0:
            actions.append(
                {
                    "key": "review_submissions",
                    "title": "处理待审阅提交",
                    "count": overview["pending_submissions"],
                    "route": "/teacher/evaluations",
                    "priority": "high",
                }
            )
        if overview["draft_evaluations"] > 0:
            actions.append(
                {
                    "key": "confirm_evaluations",
                    "title": "确认评价反馈",
                    "count": overview["draft_evaluations"],
                    "route": "/teacher/evaluations",
                    "priority": "high",
                }
            )
        if overview["draft_tasks"] > 0:
            actions.append(
                {
                    "key": "publish_tasks",
                    "title": "发布草稿任务",
                    "count": overview["draft_tasks"],
                    "route": "/teacher/projects",
                    "priority": "medium",
                }
            )
        if not actions:
            actions.append(
                {
                    "key": "start_project",
                    "title": "创建或打开跨学科项目",
                    "count": overview["active_projects"],
                    "route": "/teacher/projects",
                    "priority": "low",
                }
            )
        return actions
```

- [ ] **Step 6: Run backend tests**

Run:

```powershell
python -m pytest backend/tests/test_teacher_workflow_summary.py -q
python -m compileall backend\app
```

Expected:

- `test_teacher_workflow_summary.py` passes.
- Backend compile exits with code `0`.

## Task 3: Frontend Contract Tests

**Files:**

- Create: `backend/tests/test_teacher_page_completion.py`
- Modify later: `frontend/src/api/dashboard.ts`
- Modify later: `frontend/src/router/routes.ts`
- Modify later: `frontend/src/layouts/RoleMenu.vue`
- Create later: new teacher page components.
- Modify later: `scripts/check_frontend_route_smoke.py`

- [ ] **Step 1: Add failing frontend static contract tests**

Create `backend/tests/test_teacher_page_completion.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "frontend" / "src" / "api" / "dashboard.ts"
ROUTES = ROOT / "frontend" / "src" / "router" / "routes.ts"
MENU = ROOT / "frontend" / "src" / "layouts" / "RoleMenu.vue"
TEACHER_DIR = ROOT / "frontend" / "src" / "views" / "teacher"
ROUTE_SMOKE = ROOT / "scripts" / "check_frontend_route_smoke.py"


def test_dashboard_api_exposes_teacher_workflow_summary_contract():
    text = API.read_text(encoding="utf-8")

    for label in [
        "TeacherWorkflowSummary",
        "TeacherWorkflowOverview",
        "TeacherWorkflowNextAction",
        "TeacherWorkflowDiagnosis",
        "TeacherWorkflowClassroom",
        "TeacherWorkflowImprovements",
        "getTeacherWorkflowSummary",
        "/dashboard/teacher/workflow-summary",
    ]:
        assert label in text


def test_teacher_routes_and_menu_cover_core_loop_pages():
    routes = ROUTES.read_text(encoding="utf-8")
    menu = MENU.read_text(encoding="utf-8")

    for label in [
        "path: 'diagnosis'",
        "LearningDiagnosis.vue",
        "path: 'classroom'",
        "ClassroomImplementation.vue",
        "path: 'improvements'",
        "TeachingImprovements.vue",
    ]:
        assert label in routes

    for label in [
        "/teacher/diagnosis",
        "学情诊断与分析",
        "/teacher/classroom",
        "课堂实施工具",
        "/teacher/improvements",
        "教学改进建议",
    ]:
        assert label in menu

    assert "学校管理" not in menu
    assert "区域驾驶舱" not in menu


def test_teacher_core_loop_pages_have_visible_anchors():
    pages = {
        "TeacherDashboard.vue": ["教师工作台", "今日待办", "教学闭环", "下一步"],
        "LearningDiagnosis.vue": ["学情诊断与分析", "学习证据", "任务完成情况", "评价维度表现"],
        "ClassroomImplementation.vue": ["课堂实施工具", "已发布任务", "提交进度", "进入审阅"],
        "TeachingImprovements.vue": ["教学改进建议", "改进清单", "建议动作", "关联入口"],
    }

    for filename, labels in pages.items():
        path = TEACHER_DIR / filename
        assert path.exists(), f"Missing teacher page: {path}"
        text = path.read_text(encoding="utf-8")
        for label in labels:
            assert label in text


def test_route_smoke_protects_teacher_core_loop_pages():
    text = ROUTE_SMOKE.read_text(encoding="utf-8")

    for label in [
        "LearningDiagnosis.vue",
        "ClassroomImplementation.vue",
        "TeachingImprovements.vue",
        "学情诊断与分析",
        "课堂实施工具",
        "教学改进建议",
    ]:
        assert label in text
```

- [ ] **Step 2: Run tests and confirm red**

Run:

```powershell
python -m pytest backend/tests/test_teacher_page_completion.py -q
```

Expected:

- Fails because the API types, routes, menu entries, page components, and route smoke anchors do not exist yet.

## Task 4: Frontend API Types, Routes, and Menu

**Files:**

- Modify: `frontend/src/api/dashboard.ts`
- Modify: `frontend/src/router/routes.ts`
- Modify: `frontend/src/layouts/RoleMenu.vue`
- Modify: `scripts/check_frontend_route_smoke.py`
- Test: `backend/tests/test_teacher_page_completion.py`

- [ ] **Step 1: Add workflow summary types and API helper**

In `frontend/src/api/dashboard.ts`, add:

```ts
export interface TeacherWorkflowOverview {
  active_projects: number
  draft_tasks: number
  published_tasks: number
  pending_submissions: number
  draft_evaluations: number
  confirmed_evaluations: number
  available_resources: number
}

export interface TeacherWorkflowNextAction {
  key: string
  title: string
  count: number
  route: string
  priority: 'high' | 'medium' | 'low'
}

export interface TeacherWorkflowClassSignal {
  key: string
  title: string
  value: number
  description: string
  route: string
}

export interface TeacherWorkflowTaskCompletion {
  task_id: string
  task_title: string
  project_name: string
  status: string
  submission_count: number
  route: string
}

export interface TeacherWorkflowRubricSignal {
  dimension: string
  average_score: number
  max_score: number
  level: string
  description: string
}

export interface TeacherWorkflowDiagnosis {
  class_signals: TeacherWorkflowClassSignal[]
  task_completion: TeacherWorkflowTaskCompletion[]
  rubric_signals: TeacherWorkflowRubricSignal[]
}

export interface TeacherWorkflowClassroomTask {
  task_id: string
  task_title: string
  project_id: string
  project_name: string
  task_type: string
  due_at: string | null
  submission_count: number
  review_route: string
  project_route: string
}

export interface TeacherWorkflowClassroom {
  active_task_cards: TeacherWorkflowClassroomTask[]
}

export interface TeacherWorkflowSuggestion {
  key: string
  title: string
  description: string
  route: string
  priority: 'high' | 'medium' | 'low'
}

export interface TeacherWorkflowImprovements {
  suggestions: TeacherWorkflowSuggestion[]
}

export interface TeacherWorkflowSummary {
  overview: TeacherWorkflowOverview
  next_actions: TeacherWorkflowNextAction[]
  diagnosis: TeacherWorkflowDiagnosis
  classroom: TeacherWorkflowClassroom
  improvements: TeacherWorkflowImprovements
}

export function getTeacherWorkflowSummary(): Promise<ApiResponse<TeacherWorkflowSummary>> {
  return request.get('/dashboard/teacher/workflow-summary')
}
```

- [ ] **Step 2: Add teacher routes**

In `frontend/src/router/routes.ts`, add these children under `/teacher`:

```ts
      {
        path: 'diagnosis',
        name: 'LearningDiagnosis',
        component: () => import('@/views/teacher/LearningDiagnosis.vue'),
        meta: { title: '学情诊断与分析' }
      },
      {
        path: 'classroom',
        name: 'ClassroomImplementation',
        component: () => import('@/views/teacher/ClassroomImplementation.vue'),
        meta: { title: '课堂实施工具' }
      },
      {
        path: 'improvements',
        name: 'TeachingImprovements',
        component: () => import('@/views/teacher/TeachingImprovements.vue'),
        meta: { title: '教学改进建议' }
      },
```

Place them near the existing teacher workflow routes, after `ai/lesson-plan` and before `evaluations`.

- [ ] **Step 3: Update teacher menu entries**

In `frontend/src/layouts/RoleMenu.vue`, update `teacherSections` so the core section uses real routes:

```ts
const teacherSections: MenuSection[] = [
  {
    title: '教学核心应用',
    items: [
      { index: '/teacher', label: '工作台', icon: Grid, actionable: true },
      { index: '/teacher/ai/lesson-plan', label: 'AI生成教学方案', icon: Document, actionable: true },
      { index: '/teacher/projects', label: '跨学科任务设计', icon: Management, actionable: true },
      { index: '/teacher/diagnosis', label: '学情诊断与分析', icon: DataAnalysis, actionable: true },
      { index: '/teacher/classroom', label: '课堂实施工具', icon: ChatDotRound, actionable: true },
      { index: '/teacher/evaluations', label: '智能评价与反馈', icon: Checked, actionable: true },
      { index: '/teacher/improvements', label: '教学改进建议', icon: TrendCharts, actionable: true }
    ]
  },
  {
    title: '资源与知识库',
    items: [
      { index: '/teacher/resources?type=region', label: '区域教材中心', icon: Files },
      { index: '/teacher/resources', label: '教学资源库', icon: Folder },
      { index: '/teacher/resources?type=questions', label: '题库中心', icon: Notebook },
      { index: '/teacher/resources?type=cases', label: '案例库', icon: Collection },
      { index: '/teacher/resources?type=video', label: '微课资源', icon: Monitor }
    ]
  },
  {
    title: '数据与设置',
    items: [
      { index: '/teacher/data', label: '班级数据看板', icon: DataBoard, actionable: true },
      { index: '/teacher/settings', label: '系统设置', icon: Setting, actionable: true }
    ]
  }
]
```

Also extend `availableRoots`:

```ts
const availableRoots = [
  '/teacher',
  '/teacher/ai/lesson-plan',
  '/teacher/projects',
  '/teacher/diagnosis',
  '/teacher/classroom',
  '/teacher/evaluations',
  '/teacher/improvements',
  '/teacher/resources',
  '/teacher/data',
  '/teacher/settings',
  '/student',
  '/student/tasks',
  '/student/profile',
  '/research',
  '/research/templates',
  '/research/resources',
  '/admin',
  '/admin/trial-delivery',
  '/admin/users',
  '/admin/schools',
  '/admin/ai-agents',
  '/admin/ai-calls',
  '/admin/audit-logs',
  '/admin/settings'
]
```

And update `activeMenu`:

```ts
const activeMenu = computed(() => {
  if (route.path.startsWith('/teacher/ai/lesson-plan')) return '/teacher/ai/lesson-plan'
  if (route.path.startsWith('/teacher/diagnosis')) return '/teacher/diagnosis'
  if (route.path.startsWith('/teacher/classroom')) return '/teacher/classroom'
  if (route.path.startsWith('/teacher/evaluations')) return '/teacher/evaluations'
  if (route.path.startsWith('/teacher/improvements')) return '/teacher/improvements'
  if (route.path.startsWith('/teacher/projects')) return '/teacher/projects'
  if (route.path.startsWith('/teacher/resources')) return '/teacher/resources'
  return route.path
})
```

- [ ] **Step 4: Update route smoke expectations**

In `scripts/check_frontend_route_smoke.py`, add route expectations for:

```python
RouteExpectation("path: 'diagnosis'", "views/teacher/LearningDiagnosis.vue", "学情诊断与分析", ("学情诊断与分析", "学习证据", "任务完成情况", "评价维度表现")),
RouteExpectation("path: 'classroom'", "views/teacher/ClassroomImplementation.vue", "课堂实施工具", ("课堂实施工具", "已发布任务", "提交进度", "进入审阅")),
RouteExpectation("path: 'improvements'", "views/teacher/TeachingImprovements.vue", "教学改进建议", ("教学改进建议", "改进清单", "建议动作", "关联入口")),
```

Also expand the existing `/teacher` dashboard expectation to include:

```python
("教师工作台", "今日待办", "教学闭环", "下一步")
```

- [ ] **Step 5: Run frontend contract test and confirm only page anchors remain failing**

Run:

```powershell
python -m pytest backend/tests/test_teacher_page_completion.py -q
```

Expected:

- API type, route, and menu assertions should pass.
- Page anchor assertions may still fail until Task 5 and Task 6 create/update the Vue files.

## Task 5: Shared Frontend Loading Pattern and Dashboard Rewrite

**Files:**

- Modify: `frontend/src/views/teacher/TeacherDashboard.vue`
- Test: `backend/tests/test_teacher_page_completion.py`

- [ ] **Step 1: Replace dashboard data source with workflow summary**

In `frontend/src/views/teacher/TeacherDashboard.vue`, import:

```ts
import { getTeacherWorkflowSummary, type TeacherWorkflowSummary } from '@/api/dashboard'
```

Use this initial state:

```ts
const summary = ref<TeacherWorkflowSummary>({
  overview: {
    active_projects: 0,
    draft_tasks: 0,
    published_tasks: 0,
    pending_submissions: 0,
    draft_evaluations: 0,
    confirmed_evaluations: 0,
    available_resources: 0
  },
  next_actions: [],
  diagnosis: {
    class_signals: [],
    task_completion: [],
    rubric_signals: []
  },
  classroom: {
    active_task_cards: []
  },
  improvements: {
    suggestions: []
  }
})
```

Add:

```ts
const loading = ref(false)

async function loadSummary() {
  loading.value = true
  try {
    const response = await getTeacherWorkflowSummary()
    summary.value = response.data
  } finally {
    loading.value = false
  }
}

onMounted(loadSummary)
```

- [ ] **Step 2: Render dashboard anchors and workflow hub**

Ensure the template contains these visible anchors:

```vue
<h1>教师工作台</h1>
<h2>今日待办</h2>
<h2>教学闭环</h2>
<h2>下一步</h2>
```

Render:

- Summary cards from `summary.overview`.
- Next-action list from `summary.next_actions`.
- Teaching-loop steps with routes:
  - `/teacher/diagnosis`
  - `/teacher/ai/lesson-plan`
  - `/teacher/projects`
  - `/teacher/classroom`
  - `/teacher/evaluations`
  - `/teacher/improvements`

Use `router.push(action.route)` for action buttons.

- [ ] **Step 3: Run static dashboard test**

Run:

```powershell
python -m pytest backend/tests/test_teacher_page_completion.py::test_teacher_core_loop_pages_have_visible_anchors -q
```

Expected:

- Still fails for missing new pages.
- `TeacherDashboard.vue` anchor assertions should pass.

## Task 6: New Teacher Core Loop Pages

**Files:**

- Create: `frontend/src/views/teacher/LearningDiagnosis.vue`
- Create: `frontend/src/views/teacher/ClassroomImplementation.vue`
- Create: `frontend/src/views/teacher/TeachingImprovements.vue`
- Test: `backend/tests/test_teacher_page_completion.py`

- [ ] **Step 1: Create LearningDiagnosis.vue**

Create `frontend/src/views/teacher/LearningDiagnosis.vue`:

```vue
<template>
  <div class="teacher-page" v-loading="loading">
    <header class="page-header">
      <p>教学证据</p>
      <h1>学情诊断与分析</h1>
      <span>基于项目、任务提交和评价记录，帮助教师发现需要跟进的教学证据。</span>
    </header>

    <section class="summary-grid">
      <article v-for="signal in summary.diagnosis.class_signals" :key="signal.key" class="summary-card">
        <span>{{ signal.title }}</span>
        <strong>{{ signal.value }}</strong>
        <p>{{ signal.description }}</p>
        <el-button text type="primary" @click="go(signal.route)">查看关联入口</el-button>
      </article>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>学习证据</h2>
        <el-button :icon="Refresh" circle @click="loadSummary" />
      </div>
      <el-table :data="summary.diagnosis.task_completion" empty-text="暂无任务完成情况">
        <el-table-column prop="project_name" label="项目" min-width="160" />
        <el-table-column prop="task_title" label="任务" min-width="180" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column prop="submission_count" label="提交数" width="100" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="go(row.route)">进入审阅</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="panel">
      <h2>任务完成情况</h2>
      <div class="signal-list">
        <article v-for="item in summary.diagnosis.task_completion" :key="item.task_id" class="signal-card">
          <strong>{{ item.task_title }}</strong>
          <span>{{ item.project_name }} · {{ item.submission_count }} 份提交</span>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2>评价维度表现</h2>
      <el-empty v-if="!summary.diagnosis.rubric_signals.length" description="暂无需要重点跟进的评价维度" />
      <div v-else class="signal-list">
        <article v-for="signal in summary.diagnosis.rubric_signals" :key="signal.dimension" class="signal-card">
          <strong>{{ signal.dimension }}</strong>
          <span>{{ signal.average_score }} / {{ signal.max_score }}</span>
          <p>{{ signal.description }}</p>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { getTeacherWorkflowSummary, type TeacherWorkflowSummary } from '@/api/dashboard'

const router = useRouter()
const loading = ref(false)
const summary = ref<TeacherWorkflowSummary>({
  overview: { active_projects: 0, draft_tasks: 0, published_tasks: 0, pending_submissions: 0, draft_evaluations: 0, confirmed_evaluations: 0, available_resources: 0 },
  next_actions: [],
  diagnosis: { class_signals: [], task_completion: [], rubric_signals: [] },
  classroom: { active_task_cards: [] },
  improvements: { suggestions: [] }
})

async function loadSummary() {
  loading.value = true
  try {
    const response = await getTeacherWorkflowSummary()
    summary.value = response.data
  } finally {
    loading.value = false
  }
}

function go(route: string) {
  router.push(route)
}

onMounted(loadSummary)
</script>

<style scoped>
.teacher-page { display: grid; gap: 16px; }
.page-header { display: grid; gap: 6px; }
.page-header p { margin: 0; color: #1f6feb; font-size: 13px; }
.page-header h1 { margin: 0; color: #152b4a; }
.page-header span { color: #5b6b80; }
.summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.summary-card, .panel, .signal-card { border: 1px solid #e3ebf6; border-radius: 8px; background: #fff; padding: 14px; }
.summary-card { display: grid; gap: 8px; }
.summary-card strong { font-size: 28px; color: #152b4a; }
.summary-card p, .signal-card p { margin: 0; color: #5b6b80; }
.panel { display: grid; gap: 12px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; }
.panel h2 { margin: 0; color: #152b4a; font-size: 18px; }
.signal-list { display: grid; gap: 10px; }
.signal-card { display: grid; gap: 6px; }
.signal-card span { color: #1f6feb; font-size: 13px; }
@media (max-width: 900px) { .summary-grid { grid-template-columns: 1fr; } }
</style>
```

- [ ] **Step 2: Create ClassroomImplementation.vue**

Create `frontend/src/views/teacher/ClassroomImplementation.vue` with visible anchors `课堂实施工具`, `已发布任务`, `提交进度`, and `进入审阅`. Use `summary.classroom.active_task_cards` from `getTeacherWorkflowSummary()` and route buttons to `card.project_route` and `card.review_route`.

Use this core card template:

```vue
<article v-for="card in summary.classroom.active_task_cards" :key="card.task_id" class="task-card">
  <strong>{{ card.task_title }}</strong>
  <span>{{ card.project_name }} · {{ card.task_type }}</span>
  <p>提交进度：{{ card.submission_count }} 份提交</p>
  <div class="card-actions">
    <el-button @click="go(card.project_route)">查看项目</el-button>
    <el-button type="primary" @click="go(card.review_route)">进入审阅</el-button>
  </div>
</article>
```

Include an empty state:

```vue
<el-empty v-if="!summary.classroom.active_task_cards.length" description="暂无已发布任务，请先在项目详情中发布学习任务" />
```

- [ ] **Step 3: Create TeachingImprovements.vue**

Create `frontend/src/views/teacher/TeachingImprovements.vue` with visible anchors `教学改进建议`, `改进清单`, `建议动作`, and `关联入口`. Use `summary.improvements.suggestions` from `getTeacherWorkflowSummary()`.

Use this core suggestion template:

```vue
<article v-for="item in summary.improvements.suggestions" :key="item.key" class="suggestion-card">
  <el-tag :type="item.priority === 'high' ? 'danger' : item.priority === 'medium' ? 'warning' : 'success'">
    {{ item.priority }}
  </el-tag>
  <strong>{{ item.title }}</strong>
  <p>{{ item.description }}</p>
  <el-button type="primary" @click="go(item.route)">关联入口</el-button>
</article>
```

- [ ] **Step 4: Run frontend static tests**

Run:

```powershell
python -m pytest backend/tests/test_teacher_page_completion.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q
```

Expected:

- All pass.

## Task 7: Frontend Build and Browser Smoke

**Files:**

- No new files unless browser smoke exposes an issue.

- [ ] **Step 1: Run frontend build**

Run:

```powershell
cd frontend
npm run build
cd ..
```

Expected:

- `vue-tsc` passes.
- Vite build exits with code `0`.
- Existing Rollup/Sass/chunk warnings are acceptable if no new errors appear.

- [ ] **Step 2: Browser smoke teacher routes**

Use the in-app browser as `teacher001/password`.

Open:

```text
http://127.0.0.1:3000/teacher
http://127.0.0.1:3000/teacher/diagnosis
http://127.0.0.1:3000/teacher/classroom
http://127.0.0.1:3000/teacher/improvements
```

Confirm:

- `/teacher` renders `教师工作台`, `今日待办`, `教学闭环`, `下一步`.
- `/teacher/diagnosis` renders `学情诊断与分析`, `学习证据`, `任务完成情况`, `评价维度表现`.
- `/teacher/classroom` renders `课堂实施工具`, `已发布任务`, `提交进度`, `进入审阅`.
- `/teacher/improvements` renders `教学改进建议`, `改进清单`, `建议动作`, `关联入口`.
- Browser console has no errors or warnings.

## Task 8: Release Verification and Closeout

**Files:**

- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`
- Modify: `docs/superpowers/plans/2026-05-29-teacher-side-core-loop.md`

- [ ] **Step 1: Run full release gate**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-release.ps1
```

Expected:

- Backend tests pass.
- Backend compile passes.
- Frontend text health passes.
- Frontend route smoke passes.
- Frontend build passes.

- [ ] **Step 2: Update progress doc**

Add a new P13 section in `docs/superpowers/progress/2026-05-25-platform-progress.md`:

```markdown
- [ ] Phase 13: Complete teacher-side workflow pages and menu reachability.
  - [x] Add P13 teacher-side completion design.
  - [x] Write P13 Batch 1 implementation plan.
  - [x] Add teacher workflow summary endpoint.
  - [x] Add teacher dashboard, diagnosis, classroom, and improvement pages.
  - [x] Run release verification and browser smoke.
```

Add a completed-work note with the exact release-gate output and browser-smoke result.

- [ ] **Step 3: Mark this implementation plan complete**

In this file, mark completed steps with `[x]` as each step is verified.

- [ ] **Step 4: Commit and push**

Run:

```powershell
git status --short
git add backend/app/api/routers/dashboard.py backend/app/services/dashboard_service.py backend/tests/test_teacher_workflow_summary.py backend/tests/test_teacher_page_completion.py frontend/src/api/dashboard.ts frontend/src/router/routes.ts frontend/src/layouts/RoleMenu.vue frontend/src/views/teacher/TeacherDashboard.vue frontend/src/views/teacher/LearningDiagnosis.vue frontend/src/views/teacher/ClassroomImplementation.vue frontend/src/views/teacher/TeachingImprovements.vue scripts/check_frontend_route_smoke.py docs/superpowers/progress/2026-05-25-platform-progress.md docs/superpowers/plans/2026-05-29-teacher-side-core-loop.md
git commit -m "Add teacher-side core workflow pages"
git push
```

Expected:

- Commit succeeds.
- Push updates `codex/agent-contract-crud`.
- Final `git status --short --branch` shows a clean branch tracking origin.

## Self-Review

- Spec coverage: Covers P13 Batch 1 core loop enhancement from the design spec: teacher workflow summary endpoint, dashboard hub, learning diagnosis, classroom implementation, teaching improvement, menu reachability, tests, release verification, and browser smoke.
- Placeholder scan: No TODO/TBD placeholders or deferred implementation steps remain.
- Type consistency: Backend keys match frontend interfaces: `overview`, `next_actions`, `diagnosis`, `classroom`, `improvements`.
- Scope control: Resource subroutes, question bank, case library, micro-lessons, and teacher data-center deepening remain P13 Batch 2.
