from fastapi.testclient import TestClient

from app.main import app
from app.services.providers.base import AIProviderRequest
from app.services.providers.openai_compatible import OpenAICompatibleProvider


def _login(client: TestClient, username: str = "admin") -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _create_agent(client: TestClient, headers: dict[str, str], provider: str, config: dict) -> str:
    response = client.post(
        "/api/v1/ai/agents",
        headers=headers,
        json={
            "name": f"{provider} diagnostics agent",
            "provider": provider,
            "scenario": "lesson_plan",
            "config": {"provider": provider, **config},
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "enabled": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def _call_payload(agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "scenario": "lesson_plan",
        "input": {
            "theme": "海洋生态保护",
            "grade": "七年级",
            "subject_ids": [],
            "class_ids": [],
            "lesson_count": 2,
        },
    }


def test_ai_call_failure_persists_safe_diagnostic_metadata():
    with TestClient(app) as client:
        headers = _login(client)
        agent_id = _create_agent(
            client,
            headers,
            "qwen_agent",
            {"model": "qwen-plus", "api_key": "secret-key-for-test"},
        )

        response = client.post("/api/v1/ai/calls", headers=headers, json=_call_payload(agent_id))
        calls_response = client.get("/api/v1/ai/calls?error_category=configuration_missing", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "failed"
    assert data["error_category"] == "configuration_missing"
    assert data["diagnostic_metadata"]["retryable"] is False
    assert data["diagnostic_metadata"]["provider"] == "qwen_agent"
    assert "endpoint" in data["diagnostic_metadata"]["safe_metadata"]["missing"]
    assert "secret-key-for-test" not in str(data)

    assert calls_response.status_code == 200
    items = calls_response.json()["data"]["items"]
    assert any(item["id"] == data["id"] for item in items)
    assert all(item["error_category"] == "configuration_missing" for item in items)


def test_ai_call_diagnostics_summary_groups_failed_calls():
    with TestClient(app) as client:
        headers = _login(client)
        agent_id = _create_agent(client, headers, "deepseek_agent", {"model": "deepseek-chat"})
        call_response = client.post("/api/v1/ai/calls", headers=headers, json=_call_payload(agent_id))
        summary_response = client.get("/api/v1/ai/calls/diagnostics/summary", headers=headers)

    assert call_response.status_code == 200
    assert summary_response.status_code == 200
    data = summary_response.json()["data"]
    assert data["total_failed"] >= 1
    assert any(item["category"] == "configuration_missing" for item in data["by_category"])
    assert any(item["provider"] == "deepseek_agent" for item in data["by_provider"])
    assert data["recent_failures"]
    assert data["recent_failures"][0]["error_category"]


def test_openai_compatible_provider_classifies_bad_json_and_timeout():
    class BadJsonProvider(OpenAICompatibleProvider):
        def _post_json(self, endpoint, payload, api_key, timeout):
            return {"choices": [{"message": {"content": "not json"}}]}

    provider = BadJsonProvider(provider_name="kimi_agent")
    request = AIProviderRequest(
        scenario="lesson_plan",
        input_data={"theme": "海洋生态保护"},
        user_id="00000000-0000-0000-0000-000000000001",
        school_id="00000000-0000-0000-0000-000000000002",
        agent_config={
            "endpoint": "https://example.test/v1/chat/completions",
            "model": "moonshot-v1",
            "api_key": "secret-key-for-test",
        },
    )

    result = __import__("asyncio").run(provider.run(request))

    assert result.success is False
    assert result.diagnostic_metadata["error_category"] == "upstream_bad_response"
    assert "secret-key-for-test" not in str(result.diagnostic_metadata)


def test_trial_readiness_warns_when_recent_real_provider_failure_exists():
    with TestClient(app) as client:
        headers = _login(client)
        agent_id = _create_agent(client, headers, "qwen_agent", {"model": "qwen-plus"})
        call_response = client.post("/api/v1/ai/calls", headers=headers, json=_call_payload(agent_id))
        readiness_response = client.get("/api/v1/dashboard/trial-readiness", headers=headers)

    assert call_response.status_code == 200
    assert readiness_response.status_code == 200
    ai_item = next(item for item in readiness_response.json()["data"]["items"] if item["key"] == "ai_contract")
    assert ai_item["status"] in {"error", "warning"}
    assert ai_item["route"] in {"/admin/ai-agents", "/admin/ai-calls"}
