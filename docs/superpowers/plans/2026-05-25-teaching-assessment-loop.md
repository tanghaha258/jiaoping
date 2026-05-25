# Teaching Assessment Loop Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the student submission and teacher evaluation loop so adopted projects can operate through real teaching-assessment workflows.

**Architecture:** Keep backend APIs role-scoped and transaction-light. Frontend pages use list/detail/dialog hierarchy and real API empty states, with no demo fallback data.

**Tech Stack:** FastAPI, SQLAlchemy async, Vue 3, Element Plus, Vite, pytest.

---

### Task 1: Backend Student Submission and Feedback Flow

**Files:**
- Modify: `backend/app/services/student_service.py`
- Modify: `backend/app/services/evaluation_service.py`
- Modify: `backend/app/api/routers/evaluations.py`
- Test: `backend/tests/test_student_feedback_flow.py`

- [x] Step 1: Add failing tests for `/student/submissions`, teacher evaluation confirmation, and student-scoped evaluation visibility.
- [x] Step 2: Run the new test and confirm it fails because `StudentService.list_student_submissions` is not exposed correctly or evaluation scoping is incomplete.
- [x] Step 3: Move `list_student_submissions` back into `StudentService` and ensure it formats the current student's records.
- [x] Step 4: Add role-scoped evaluation list/detail behavior: students only see evaluations for their own submissions.
- [x] Step 5: Run the new test until it passes, then run all backend tests.

### Task 2: Teacher Submission Review Workbench

**Files:**
- Modify: `frontend/src/views/teacher/SubmissionReview.vue`
- Modify: `frontend/src/api/evaluations.ts`

- [x] Step 1: Remove demo/fallback logic and clean visible Chinese copy.
- [x] Step 2: Keep task header, submission table, detail drawer, and evaluation dialog.
- [x] Step 3: Use task rubric by default and submit backend `scores` dictionary.
- [x] Step 4: Reload submissions after evaluation so reviewed status is visible.
- [x] Step 5: Run `npm run build`.

### Task 3: Teacher Evaluation Center Ledger

**Files:**
- Modify: `frontend/src/views/teacher/EvaluationCenter.vue`
- Modify: `frontend/src/api/evaluations.ts`

- [x] Step 1: Replace demo fallback with real empty state.
- [x] Step 2: Add filters for status and evaluator type supported by the API.
- [x] Step 3: Show computed total score and score dimension detail drawer.
- [x] Step 4: Confirm draft evaluations from the ledger and reload.
- [x] Step 5: Run `npm run build`.

### Task 4: Student Task and Feedback UI

**Files:**
- Modify: `frontend/src/views/student/StudentTaskList.vue`
- Modify: `frontend/src/views/student/StudentTaskDetail.vue`
- Modify: `frontend/src/views/student/SubmissionDetail.vue`

- [x] Step 1: Ensure student task list uses real `/student/tasks` fields, including submission status.
- [x] Step 2: Ensure task detail allows submit/resubmit only when task is published.
- [x] Step 3: Show submission detail with confirmed feedback cards.
- [x] Step 4: Remove any demo fallback behavior and use explicit empty states.
- [x] Step 5: Run `npm run build`.

### Task 5: Verification, Browser Smoke, Commit, Push

**Files:**
- Modify: `docs/superpowers/progress/2026-05-25-platform-progress.md`

- [x] Step 1: Run `python -m pytest backend/tests -q`.
- [x] Step 2: Run `python -m compileall backend\app`.
- [x] Step 3: Run `npm run build`.
- [x] Step 4: Browser smoke teacher review/evaluation pages and student task/submission pages.
- [x] Step 5: Update progress document.
- [x] Step 6: Commit and push branch `codex/agent-contract-crud`.
