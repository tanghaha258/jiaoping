# P13 Teacher-Side Completion Design

## Goal

Complete the teacher-side product surface so every teacher menu entry maps to a real, explainable workflow while the core teaching-assessment loop becomes smoother for trial demonstrations and daily use.

## Current Context

The platform already has the essential teacher workflow:

- `/teacher`: teacher dashboard.
- `/teacher/projects`: project list and creation.
- `/teacher/projects/:id`: project detail and task management.
- `/teacher/ai/lesson-plan`: AI lesson-plan generation and teacher adoption.
- `/teacher/tasks/:id/submissions`: submission review.
- `/teacher/evaluations`: evaluation ledger and confirmation.
- `/teacher/resources`: resource CRUD.
- `/teacher/data`: thin data page.
- `/teacher/settings`: password/settings page.

The gap is not a missing backend foundation. The gap is product completeness:

- Several teacher menu items only route to an existing page with query parameters and do not create a distinct experience.
- Learning diagnosis, classroom implementation, and improvement suggestions are important PRD workflow stages but do not have dedicated teacher surfaces.
- Resource subareas such as regional teaching materials, question bank, case library, and micro-lesson resources are not presented as separate teacher workflows.
- The teacher dashboard should become a workflow hub for what the teacher needs to do next, not only a static overview.

## Product Direction

P13 uses a business-enhanced approach:

- Every teacher menu entry should become a real page or a clearly differentiated page mode.
- Core loop pages should be backed by real project/task/submission/evaluation/resource data.
- New backend work should be limited to deterministic aggregation endpoints. P13 does not add AI calls, mutable acceptance states, signed forms, or full new domain tables.
- The teacher flow should read as:

```text
Learning diagnosis -> AI lesson planning -> task design -> classroom implementation
-> submission review -> evaluation confirmation -> improvement suggestions
```

## Batch 1: Core Teaching Loop Enhancement

Batch 1 focuses on the pages most visible in a trial or real teacher workflow.

### Teacher Workflow Summary Endpoint

Add one teacher-scoped aggregation endpoint:

- Backend route: `GET /api/v1/dashboard/teacher/workflow-summary`
- Allowed role: `teacher`
- Data source: existing projects, tasks, submissions, evaluations, resources, and current user scope.
- Purpose: provide deterministic data for dashboard, diagnosis, classroom, and improvement pages.

Suggested response shape:

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
    "class_signals": [],
    "task_completion": [],
    "rubric_signals": []
  },
  "classroom": {
    "active_task_cards": []
  },
  "improvements": {
    "suggestions": []
  }
}
```

The endpoint should not infer sensitive student conclusions or high-stakes labels. It only summarizes operational teaching signals such as missing submissions, draft evaluations, low-scoring rubric dimensions, and resource gaps.

### Teacher Dashboard

Rewrite `/teacher` as a teacher workflow hub.

Expected sections:

- Today's work queue: pending submissions, draft evaluations, draft tasks, active projects.
- Current teaching loop: project -> AI lesson plan -> task -> submission -> evaluation -> improvement.
- Quick actions: create project, generate lesson plan, review submissions, open improvement suggestions.
- Recent project cards with status and next action.

The dashboard should not become a decorative landing page. It should be a compact operational workbench.

### Learning Diagnosis Page

Add a dedicated route and page:

- Route: `/teacher/diagnosis`
- Component: `frontend/src/views/teacher/LearningDiagnosis.vue`
- Menu label: `学情诊断与分析`

Expected content:

- Diagnosis summary cards from workflow summary.
- Class/task completion view.
- Rubric signal list showing dimensions that need attention.
- Student/task evidence links that navigate back to existing submission or evaluation pages.

This is not a medical or psychological diagnosis page. Wording must stay teaching-focused: "学习证据", "任务完成情况", "评价维度表现", "需要跟进".

### Classroom Implementation Page

Add a dedicated route and page:

- Route: `/teacher/classroom`
- Component: `frontend/src/views/teacher/ClassroomImplementation.vue`
- Menu label: `课堂实施工具`

Expected content:

- Active published tasks grouped by project.
- Submission progress and due-date signals.
- Quick links to project detail and submission review.
- Lightweight classroom activity cards derived from existing task metadata.

P13 does not build real-time classroom interaction, live polling, or websocket tools. The page is a classroom operations board for currently published tasks.

### Teaching Improvement Page

Add a dedicated route and page:

- Route: `/teacher/improvements`
- Component: `frontend/src/views/teacher/TeachingImprovements.vue`
- Menu label: `教学改进建议`

Expected content:

- Rule-based improvement suggestions from workflow summary.
- Suggested follow-up action for each issue.
- Links to resources, evaluations, project detail, or submission review.

Suggestions should be deterministic and explainable, for example:

- "有 3 条提交尚未评价，建议先完成反馈闭环。"
- "某评价维度近期得分偏低，建议补充示例资源或调整下一课任务说明。"
- "存在已发布但提交数为 0 的任务，建议检查任务说明和截止时间。"

No AI generation is required in P13 Batch 1.

## Batch 2: Teacher Resource and Data Surface Completion

Batch 2 focuses on menu completeness and resource-category clarity.

### Resource Subareas

Keep the existing resource CRUD model and reuse `GET /resources` filters. Add route-level or page-mode distinctions:

- `/teacher/resources/region`: regional and system-visible teaching materials.
- `/teacher/resources`: teacher's general teaching resource library.
- `/teacher/resources/questions`: question bank using `resource_type=question`.
- `/teacher/resources/cases`: case library using `resource_type=case`.
- `/teacher/resources/videos`: micro-lesson resources using `resource_type=video`.

These can share a reusable resource page component or a mode-aware `ResourceCenter.vue`, but the visible title, filters, empty state, and action copy must differ by mode.

Resource modes should support:

- Listing resources by type/visibility.
- Creating and editing personal/school resources where permissions allow.
- Clear empty states explaining what belongs in that resource area.
- Route-smoke anchors for each visible mode.

### Teacher Data Center

Strengthen `/teacher/data` into a real class data board:

- Use the workflow summary endpoint for class/task/evaluation signals.
- Show project progress, task publication/submission status, and evaluation confirmation state.
- Remove or rename menu entries that imply school-admin or regional-admin power from the teacher role.

Recommended menu cleanup:

- Keep `班级数据看板`.
- Remove `学校管理` and `区域驾驶舱` from the teacher menu, or move them behind admin roles.
- If retained for demo copy, rename them to teacher-scoped wording such as `任教班级概览`.

## Navigation Design

Teacher menu should become:

- Teaching loop:
  - 工作台 -> `/teacher`
  - AI生成教学方案 -> `/teacher/ai/lesson-plan`
  - 跨学科任务设计 -> `/teacher/projects`
  - 学情诊断与分析 -> `/teacher/diagnosis`
  - 课堂实施工具 -> `/teacher/classroom`
  - 智能评价与反馈 -> `/teacher/evaluations`
  - 教学改进建议 -> `/teacher/improvements`
- Resources:
  - 区域教材中心 -> `/teacher/resources/region`
  - 教学资源库 -> `/teacher/resources`
  - 题库中心 -> `/teacher/resources/questions`
  - 案例库 -> `/teacher/resources/cases`
  - 微课资源 -> `/teacher/resources/videos`
- Data and settings:
  - 班级数据看板 -> `/teacher/data`
  - 系统设置 -> `/teacher/settings`

All teacher menu entries must navigate. No silent no-op menu items should remain.

## Testing Strategy

Backend tests:

- Teacher can fetch workflow summary.
- Student/admin roles cannot fetch teacher-scoped workflow summary unless explicitly allowed by existing auth policy.
- Summary contains overview, next actions, diagnosis, classroom, and improvement blocks.
- Aggregation remains safe when there are no projects, tasks, submissions, or evaluations.

Frontend static tests:

- Route and menu entries exist for diagnosis, classroom, improvements, and resource subroutes.
- New teacher pages contain expected Chinese anchors.
- Route smoke protects all new teacher routes.

Build checks:

- `python -m pytest backend/tests/test_teacher_workflow_summary.py -q`
- `python -m pytest backend/tests/test_teacher_page_completion.py backend/tests/test_frontend_route_smoke.py backend/tests/test_frontend_text_health.py -q`
- `powershell -ExecutionPolicy Bypass -File scripts/check-release.ps1`

Browser smoke:

- Log in as `teacher001`.
- Open `/teacher`, `/teacher/diagnosis`, `/teacher/classroom`, `/teacher/improvements`, `/teacher/resources/region`, `/teacher/resources/questions`, `/teacher/resources/cases`, `/teacher/resources/videos`, and `/teacher/data`.
- Confirm visible Chinese anchors render with no browser console errors or warnings.

## Scope Exclusions

P13 does not include:

- Real-time classroom interaction, websocket events, live polling, or attendance.
- Full question-bank authoring engine beyond resource-type filtering.
- AI-generated improvement suggestions.
- Student self-evaluation or peer-evaluation workflows unless already available from existing evaluation APIs.
- New school-admin or region-admin powers in the teacher role.
- PDF export, signed forms, or delivery-package changes.

## Acceptance Criteria

- Every teacher menu item opens a real route and has visible, differentiated content.
- The teacher dashboard presents next actions based on real data.
- Learning diagnosis, classroom implementation, and teaching improvement pages are backed by deterministic workflow summary data.
- Resource subareas are visible, route-protected, and mode-specific.
- Teacher menu no longer contains misleading school/region management entries.
- Release checks and browser smoke pass.

## Self-Review

- Placeholder scan: no TODO/TBD placeholders remain.
- Scope check: split into Batch 1 core loop enhancement and Batch 2 resource/data completion.
- Consistency check: route names, component names, and endpoint names are stable across sections.
- Risk check: P13 avoids adding AI calls or new domain tables, keeping the work achievable on top of existing project/task/submission/evaluation/resource data.
