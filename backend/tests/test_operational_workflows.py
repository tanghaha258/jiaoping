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


def test_resource_metadata_crud_smoke():
    with TestClient(app) as client:
        headers = _login(client, "teacher001")

        create_response = client.post(
            "/api/v1/resources",
            json={
                "title": "CRUD smoke resource",
                "resource_type": "document",
                "url": "https://example.com/crud-smoke",
                "metadata": {"source": "pytest"},
                "visibility": "school",
            },
            headers=headers,
        )
        assert create_response.status_code == 200
        resource = create_response.json()["data"]

        update_response = client.patch(
            f"/api/v1/resources/{resource['id']}",
            json={
                "title": "CRUD smoke resource updated",
                "metadata": {"source": "pytest", "updated": True},
            },
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["title"] == "CRUD smoke resource updated"

        delete_response = client.delete(
            f"/api/v1/resources/{resource['id']}",
            headers=headers,
        )
        assert delete_response.status_code == 200

        list_response = client.get(
            "/api/v1/resources",
            params={"page": 1, "page_size": 100},
            headers=headers,
        )
        assert list_response.status_code == 200
        listed_ids = {item["id"] for item in list_response.json()["data"]["items"]}
        assert resource["id"] not in listed_ids


def test_lesson_plan_adoption_creates_active_project_with_draft_tasks_hidden_from_students():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")
        student_headers = _login(client, "student001")

        options = client.get(
            "/api/v1/ai/workflows/lesson-plan/options",
            headers=teacher_headers,
        ).json()["data"]

        draft_response = client.post(
            "/api/v1/ai/workflows/lesson-plan/draft",
            json={
                "agent_id": options["agents"][0]["id"],
                "theme": "Operational adoption smoke",
                "grade": "七年级",
                "subject_ids": [item["id"] for item in options["subjects"][:2]],
                "class_ids": [options["classes"][0]["id"]],
                "lesson_count": 2,
                "core_competencies": ["问题解决", "证据表达"],
                "interdisciplinary_requirements": "融合地理与生物证据。",
                "assessment_preferences": "过程性评价与成果评价结合。",
                "resource_preferences": "任务单、资料包、展示模板。",
                "extra_requirements": "adoption smoke",
            },
            headers=teacher_headers,
        )
        assert draft_response.status_code == 200
        draft_payload = draft_response.json()["data"]

        adopt_response = client.post(
            f"/api/v1/ai/workflows/lesson-plan/{draft_payload['call_id']}/adopt",
            json={"draft": draft_payload["draft"]},
            headers=teacher_headers,
        )
        assert adopt_response.status_code == 200
        adopted = adopt_response.json()["data"]

        assert adopted["project"]["status"] == "active"
        assert len(adopted["tasks"]) == 2
        assert all(task["status"] == "draft" for task in adopted["tasks"])
        assert adopted["rubric"]["id"]
        assert adopted["resources"]

        duplicate_response = client.post(
            f"/api/v1/ai/workflows/lesson-plan/{draft_payload['call_id']}/adopt",
            json={"draft": draft_payload["draft"]},
            headers=teacher_headers,
        )
        assert duplicate_response.status_code == 200
        assert duplicate_response.json()["code"] != 0

        student_tasks_response = client.get("/api/v1/student/tasks", headers=student_headers)
        assert student_tasks_response.status_code == 200
        student_task_ids = {
            item["id"] for item in student_tasks_response.json()["data"]["items"]
        }
        adopted_task_ids = {item["id"] for item in adopted["tasks"]}
        assert adopted_task_ids.isdisjoint(student_task_ids)
