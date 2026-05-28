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
