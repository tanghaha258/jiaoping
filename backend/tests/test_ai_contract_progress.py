from fastapi.testclient import TestClient

from app.main import app


def _login_teacher(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher001", "password": "password"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_contracts_expose_lesson_plan_shape():
    with TestClient(app) as client:
        headers = _login_teacher(client)

        response = client.get("/api/v1/ai/contracts", headers=headers)

    assert response.status_code == 200
    contracts = response.json()["data"]["items"]
    lesson_contract = next(item for item in contracts if item["scenario"] == "lesson_plan")
    assert lesson_contract["version"] == "2026-05-v1"
    assert "project" in lesson_contract["output_contract"]["required"]
    assert "thinking_steps" in lesson_contract
    assert lesson_contract["thinking_steps"][0]["code"] == "understanding"


def test_ai_contracts_use_chinese_display_copy():
    english_placeholders = [
        "AI lesson-plan workflow",
        "Learning diagnosis",
        "Rubric generation",
        "Resource recommendation",
        "Teaching reflection",
        "Teacher adoption",
        "Await teacher review",
        "Understand teaching request",
    ]

    with TestClient(app) as client:
        headers = _login_teacher(client)

        response = client.get("/api/v1/ai/contracts", headers=headers)

    assert response.status_code == 200
    contracts = response.json()["data"]["items"]
    assert contracts

    for contract in contracts:
        display_text = " ".join(
            [
                contract["name"],
                contract["adoption_rule"],
                *[step["title"] for step in contract["thinking_steps"]],
                *[step.get("description", "") for step in contract["thinking_steps"]],
            ]
        )
        assert any("\u4e00" <= char <= "\u9fff" for char in contract["name"])
        assert any("\u4e00" <= char <= "\u9fff" for char in contract["adoption_rule"])
        assert all(any("\u4e00" <= char <= "\u9fff" for char in step["title"]) for step in contract["thinking_steps"])
        for phrase in english_placeholders:
            assert phrase not in display_text


def test_lesson_plan_draft_records_thinking_progress():
    with TestClient(app) as client:
        headers = _login_teacher(client)
        options = client.get("/api/v1/ai/workflows/lesson-plan/options", headers=headers).json()["data"]
        body = {
            "agent_id": options["agents"][0]["id"],
            "theme": "AI progress smoke",
            "grade": "七年级",
            "subject_ids": [item["id"] for item in options["subjects"][:2]],
            "class_ids": [options["classes"][0]["id"]],
            "lesson_count": 2,
            "core_competencies": ["问题解决"],
            "interdisciplinary_requirements": "融合地理与生物。",
            "assessment_preferences": "过程评价。",
            "resource_preferences": "任务单。",
            "extra_requirements": "progress test",
        }

        draft_response = client.post(
            "/api/v1/ai/workflows/lesson-plan/draft",
            json=body,
            headers=headers,
        )
        assert draft_response.status_code == 200
        call_id = draft_response.json()["data"]["call_id"]

        progress_response = client.get(
            f"/api/v1/ai/calls/{call_id}/progress",
            headers=headers,
        )

    assert progress_response.status_code == 200
    progress = progress_response.json()["data"]
    assert progress["call_id"] == call_id
    assert progress["percent"] == 100
    assert [step["code"] for step in progress["steps"]] == [
        "understanding",
        "retrieving_context",
        "drafting",
        "normalizing",
        "awaiting_review",
    ]
    assert all(step["status"] == "completed" for step in progress["steps"])
