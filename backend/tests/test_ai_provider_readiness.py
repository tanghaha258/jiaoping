from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import AsyncSessionFactory
from app.main import app
from app.models.ai_agent import AIAgent


def _login(client: TestClient, username: str) -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _create_agent(client: TestClient, headers: dict[str, str], provider: str, config: dict) -> str:
    response = client.post(
        "/api/v1/ai/agents",
        json={
            "name": f"{provider} readiness agent",
            "provider": provider,
            "scenario": "lesson_plan",
            "config": {"provider": provider, **config},
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "enabled": True,
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def _readiness(client: TestClient, headers: dict[str, str], agent_id: str):
    return client.get(f"/api/v1/ai/agents/{agent_id}/readiness", headers=headers)


def test_provider_readiness_reports_mock_ready_and_manual_required():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        mock_id = _create_agent(client, headers, "mock", {"model": "mock"})
        manual_id = _create_agent(client, headers, "manual_import", {"model": "manual"})

        mock_response = _readiness(client, headers, mock_id)
        manual_response = _readiness(client, headers, manual_id)

    assert mock_response.status_code == 200
    mock_data = mock_response.json()["data"]
    assert mock_data["status"] == "ready"
    assert mock_data["label"] == "配置可运行"
    assert any(item["key"] == "provider_registered" and item["status"] == "ok" for item in mock_data["checks"])

    assert manual_response.status_code == 200
    manual_data = manual_response.json()["data"]
    assert manual_data["status"] == "manual_required"
    assert manual_data["label"] == "需要人工回填"
    assert any(item["key"] == "teacher_adoption_gate" for item in manual_data["checks"])


def test_provider_readiness_accepts_seeded_string_agent_id():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        response = _readiness(client, headers, "agent-lesson-plan-0000-0000-0001")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["agent_id"] == "agent-lesson-plan-0000-0000-0001"
    assert data["status"] == "ready"


def test_provider_readiness_reports_domestic_missing_and_ready(monkeypatch):
    monkeypatch.setenv("READINESS_TEST_API_KEY", "secret-for-readiness")

    with TestClient(app) as client:
        headers = _login(client, "admin")
        missing_id = _create_agent(
            client,
            headers,
            "openai_compatible_local",
            {"model": "qwen-plus", "api_key_env": "MISSING_READINESS_KEY"},
        )
        ready_id = _create_agent(
            client,
            headers,
            "qwen_agent",
            {
                "endpoint": "https://example.test/v1/chat/completions",
                "model": "qwen-plus",
                "api_key_env": "READINESS_TEST_API_KEY",
            },
        )

        missing_response = _readiness(client, headers, missing_id)
        ready_response = _readiness(client, headers, ready_id)

    assert missing_response.status_code == 200
    missing_data = missing_response.json()["data"]
    assert missing_data["status"] == "not_configured"
    assert missing_data["label"] == "缺少配置"
    assert any(item["key"] == "endpoint" and item["status"] == "error" for item in missing_data["checks"])
    assert any(item["key"] == "api_key_env" and item["status"] == "error" for item in missing_data["checks"])

    assert ready_response.status_code == 200
    ready_data = ready_response.json()["data"]
    assert ready_data["status"] == "ready"
    assert ready_data["provider"] == "qwen_agent"
    assert any(item["key"] == "endpoint" and item["status"] == "ok" for item in ready_data["checks"])
    assert "secret-for-readiness" not in str(ready_data)


def test_provider_readiness_reports_unsupported_provider():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        agent_id = _create_agent(client, headers, "mock", {"model": "mock"})

        async def mutate_provider():
            async with AsyncSessionFactory() as session:
                result = await session.execute(select(AIAgent).where(AIAgent.id == agent_id))
                agent = result.scalar_one()
                agent.provider = "unknown_provider"
                agent.config = {"provider": "unknown_provider"}
                await session.commit()

        import asyncio

        asyncio.run(mutate_provider())
        response = _readiness(client, headers, agent_id)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "unsupported"
    assert data["label"] == "Provider未注册"
    assert any(item["key"] == "provider_registered" and item["status"] == "error" for item in data["checks"])


def test_provider_readiness_permissions_and_missing_agent():
    with TestClient(app) as client:
        admin_headers = _login(client, "admin")
        school_admin_headers = _login(client, "schooladmin")
        teacher_headers = _login(client, "teacher001")
        agent_id = _create_agent(client, admin_headers, "mock", {"model": "mock"})

        school_admin_response = _readiness(client, school_admin_headers, agent_id)
        teacher_response = _readiness(client, teacher_headers, agent_id)
        missing_response = _readiness(client, admin_headers, "00000000-0000-0000-0000-000000000000")

    assert school_admin_response.status_code == 200
    assert teacher_response.status_code == 403
    assert missing_response.status_code == 404
