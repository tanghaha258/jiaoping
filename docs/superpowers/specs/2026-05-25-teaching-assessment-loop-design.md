# Teaching Assessment Loop Phase 2 Design

## Goal

Turn the platform from "AI can create a project" into a working teaching-assessment loop: teachers publish tasks, students submit work, teachers evaluate submissions with rubrics, and students can view confirmed feedback.

## Scope

This phase focuses on the operational loop after lesson-plan adoption:

- Student task list and task detail use real task/submission APIs.
- Student submissions and resubmissions are correctly scoped to the logged-in student.
- Teacher submission review uses real submission, rubric, and evaluation APIs.
- Evaluation center uses real evaluation records and explicit empty states.
- Backend closes gaps around student submission listing and evaluation visibility.

The following remain out of scope for this phase: AI auto-grading, peer/self evaluation workflows, file upload UX, and advanced school timetable/base-data administration.

## Backend Design

`StudentService` should expose `list_student_tasks` and `list_student_submissions` as real class methods. The student task list must include the current student's submission status for each task. Student submissions must only include the current student's records.

Evaluation APIs remain generic, but student reads must be scoped: a student can only see evaluations for their own submissions, while teachers can list and confirm evaluations. Confirmed teacher evaluations are the feedback students should see.

The first backend verification target is a full API smoke path:

1. Teacher creates or uses an active project task.
2. Student submits to a published task.
3. `/student/submissions` returns that submission.
4. Teacher creates and confirms an evaluation.
5. Student can list or fetch the confirmed feedback, but not another student's feedback.

## Frontend Design

Teacher `SubmissionReview.vue` becomes the primary review workbench:

- Header shows task title and task status.
- Table lists real submissions.
- Drawer shows submitted content and current evaluation count.
- Evaluation dialog uses the task rubric when available.
- Scores are sent as the backend's `scores` dictionary.
- No demo fallbacks.

Teacher `EvaluationCenter.vue` becomes a real evaluation ledger:

- Filters by status and evaluator type.
- Table shows student, task, total score, evaluator, status, time.
- Detail drawer shows score dimensions and comments.
- Confirm action works for draft evaluations.
- Empty states explain what action creates data.

Student pages keep a simple hierarchy:

- `StudentTaskList.vue`: assigned published/closed tasks, submission status badges.
- `StudentTaskDetail.vue`: task detail, submission/resubmission dialog, existing submission state.
- `SubmissionDetail.vue`: submitted content plus confirmed feedback cards.

## Data Rules

- Draft tasks never appear in student task APIs.
- Students cannot submit to closed tasks.
- Students can update only their own submissions.
- Teachers can evaluate submissions and confirm draft evaluations.
- Student-visible feedback should be confirmed evaluations whenever possible.

## Verification

- Backend pytest for the student submission/evaluation feedback flow.
- Frontend build.
- Browser smoke for teacher submission review, evaluation center, student task list, and student task detail.
