from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_student_submission_list_and_confirmed_feedback_are_role_scoped():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")
        student_headers = _login(client, "student001")
        other_student_headers = _login(client, "student002")

        student_tasks = client.get("/api/v1/student/tasks", headers=student_headers)
        assert student_tasks.status_code == 200
        task = next(
            item for item in student_tasks.json()["data"]["items"]
            if item["status"] == "published"
        )

        submission_response = client.post(
            f"/api/v1/tasks/{task['id']}/submissions",
            json={
                "content": "Phase 2 feedback flow smoke submission",
                "group_name": "feedback-loop-group",
            },
            headers=student_headers,
        )
        assert submission_response.status_code == 200
        submission = submission_response.json()["data"]

        student_submissions = client.get("/api/v1/student/submissions", headers=student_headers)
        assert student_submissions.status_code == 200
        student_submission_ids = {
            item["id"] for item in student_submissions.json()["data"]["items"]
        }
        assert submission["id"] in student_submission_ids

        forbidden_submission = client.get(
            f"/api/v1/submissions/{submission['id']}",
            headers=other_student_headers,
        )
        assert forbidden_submission.status_code == 403
        assert forbidden_submission.json()["code"] == 403001

        rubrics = client.get("/api/v1/rubrics", headers=teacher_headers)
        assert rubrics.status_code == 200
        rubric_id = rubrics.json()["data"]["items"][0]["id"]

        evaluation_response = client.post(
            "/api/v1/evaluations",
            json={
                "submission_id": submission["id"],
                "rubric_id": rubric_id,
                "scores": {"task_understanding": 18, "evidence_expression": 17},
                "comments": "The submission includes useful evidence for the task.",
                "evaluator_type": "teacher",
            },
            headers=teacher_headers,
        )
        assert evaluation_response.status_code == 200
        evaluation_id = evaluation_response.json()["data"]["id"]

        submission_before_confirm = client.get(
            f"/api/v1/submissions/{submission['id']}",
            headers=student_headers,
        )
        assert submission_before_confirm.status_code == 200
        assert submission_before_confirm.json()["data"]["status"] == "submitted"

        tasks_waiting_for_feedback = client.get(
            "/api/v1/student/tasks",
            params={"status": "submitted", "page_size": 100},
            headers=student_headers,
        )
        assert tasks_waiting_for_feedback.status_code == 200
        waiting_feedback_task_ids = {
            item["id"] for item in tasks_waiting_for_feedback.json()["data"]["items"]
        }
        assert task["id"] in waiting_feedback_task_ids

        tasks_with_feedback_before_confirm = client.get(
            "/api/v1/student/tasks",
            params={"status": "reviewed", "page_size": 100},
            headers=student_headers,
        )
        assert tasks_with_feedback_before_confirm.status_code == 200
        feedback_task_ids_before_confirm = {
            item["id"] for item in tasks_with_feedback_before_confirm.json()["data"]["items"]
        }
        assert task["id"] not in feedback_task_ids_before_confirm

        confirm_response = client.post(
            f"/api/v1/evaluations/{evaluation_id}/confirm",
            headers=teacher_headers,
        )
        assert confirm_response.status_code == 200
        assert confirm_response.json()["data"]["status"] == "confirmed"

        submission_after_confirm = client.get(
            f"/api/v1/submissions/{submission['id']}",
            headers=student_headers,
        )
        assert submission_after_confirm.status_code == 200
        assert submission_after_confirm.json()["data"]["status"] == "reviewed"

        tasks_with_feedback_after_confirm = client.get(
            "/api/v1/student/tasks",
            params={"status": "reviewed", "page_size": 100},
            headers=student_headers,
        )
        assert tasks_with_feedback_after_confirm.status_code == 200
        feedback_task_ids_after_confirm = {
            item["id"] for item in tasks_with_feedback_after_confirm.json()["data"]["items"]
        }
        assert task["id"] in feedback_task_ids_after_confirm

        teacher_evaluations = client.get(
            "/api/v1/evaluations",
            params={"evaluator_type": "teacher"},
            headers=teacher_headers,
        )
        assert teacher_evaluations.status_code == 200
        teacher_evaluation_ids = {
            item["id"] for item in teacher_evaluations.json()["data"]["items"]
        }
        assert evaluation_id in teacher_evaluation_ids

        peer_evaluations = client.get(
            "/api/v1/evaluations",
            params={"evaluator_type": "peer"},
            headers=teacher_headers,
        )
        assert peer_evaluations.status_code == 200
        peer_evaluation_ids = {
            item["id"] for item in peer_evaluations.json()["data"]["items"]
        }
        assert evaluation_id not in peer_evaluation_ids

        student_evaluations = client.get("/api/v1/evaluations", headers=student_headers)
        assert student_evaluations.status_code == 200
        student_evaluation_ids = {
            item["id"] for item in student_evaluations.json()["data"]["items"]
        }
        assert evaluation_id in student_evaluation_ids

        other_student_evaluations = client.get("/api/v1/evaluations", headers=other_student_headers)
        assert other_student_evaluations.status_code == 200
        other_student_evaluation_ids = {
            item["id"] for item in other_student_evaluations.json()["data"]["items"]
        }
        assert evaluation_id not in other_student_evaluation_ids

        forbidden_detail = client.get(
            f"/api/v1/evaluations/{evaluation_id}",
            headers=other_student_headers,
        )
        assert forbidden_detail.status_code == 403
        assert forbidden_detail.json()["code"] == 403001


def test_student_cannot_resubmit_after_task_is_closed():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")
        student_headers = _login(client, "student001")

        projects = client.get(
            "/api/v1/projects",
            params={"status": "active", "page_size": 1},
            headers=teacher_headers,
        )
        assert projects.status_code == 200
        project_id = projects.json()["data"]["items"][0]["id"]

        task_response = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Phase 2 closed resubmit guard",
                "description": "Task used to verify closed-task resubmission guard.",
                "task_type": "individual",
                "submit_type": "text",
            },
            headers=teacher_headers,
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["data"]["id"]

        publish_response = client.post(
            f"/api/v1/tasks/{task_id}/publish",
            headers=teacher_headers,
        )
        assert publish_response.status_code == 200

        submission_response = client.post(
            f"/api/v1/tasks/{task_id}/submissions",
            json={"content": "First submitted answer for the closed task guard."},
            headers=student_headers,
        )
        assert submission_response.status_code == 200
        submission_id = submission_response.json()["data"]["id"]

        close_response = client.post(
            f"/api/v1/tasks/{task_id}/close",
            headers=teacher_headers,
        )
        assert close_response.status_code == 200

        resubmit_response = client.patch(
            f"/api/v1/submissions/{submission_id}",
            json={"content": "Attempting to change after the task has closed."},
            headers=student_headers,
        )
        assert resubmit_response.status_code == 400
        assert resubmit_response.json()["code"] == 400001


def test_student_resubmission_updates_existing_record_while_task_is_published():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")
        student_headers = _login(client, "student001")

        projects = client.get(
            "/api/v1/projects",
            params={"status": "active", "page_size": 1},
            headers=teacher_headers,
        )
        assert projects.status_code == 200
        project_id = projects.json()["data"]["items"][0]["id"]

        task_response = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Phase 2 published resubmit update",
                "description": "Task used to verify resubmission updates the same record.",
                "task_type": "individual",
                "submit_type": "text",
            },
            headers=teacher_headers,
        )
        assert task_response.status_code == 200
        task_id = task_response.json()["data"]["id"]

        publish_response = client.post(
            f"/api/v1/tasks/{task_id}/publish",
            headers=teacher_headers,
        )
        assert publish_response.status_code == 200

        submission_response = client.post(
            f"/api/v1/tasks/{task_id}/submissions",
            json={"content": "Original answer for the published resubmit update."},
            headers=student_headers,
        )
        assert submission_response.status_code == 200
        submission_id = submission_response.json()["data"]["id"]

        resubmit_response = client.patch(
            f"/api/v1/submissions/{submission_id}",
            json={"content": "Updated answer while the task is still published."},
            headers=student_headers,
        )
        assert resubmit_response.status_code == 200
        updated_submission = resubmit_response.json()["data"]
        assert updated_submission["id"] == submission_id
        assert updated_submission["content"] == "Updated answer while the task is still published."
        assert updated_submission["status"] == "submitted"
