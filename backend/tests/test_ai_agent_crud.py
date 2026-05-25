from fastapi.testclient import TestClient

from app.main import app


def _login_school_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "schooladmin", "password": "password"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_school_admin_can_soft_delete_ai_agent():
    with TestClient(app) as client:
        headers = _login_school_admin(client)
        create_response = client.post(
            "/api/v1/ai/agents",
            json={
                "name": "CRUD smoke agent",
                "provider": "mock",
                "scenario": "resource_recommendation",
                "config": {"provider": "mock", "model": "mock", "extra": {"purpose": "crud-test"}},
                "input_schema": {"type": "object", "required": ["project_id"]},
                "output_schema": {"type": "object", "required": ["resources"]},
                "enabled": True,
            },
            headers=headers,
        )
        assert create_response.status_code == 200
        agent_id = create_response.json()["data"]["id"]

        delete_response = client.delete(f"/api/v1/ai/agents/{agent_id}", headers=headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["data"]["deleted"] is True

        list_response = client.get("/api/v1/ai/agents", headers=headers)
        assert list_response.status_code == 200
        ids = [item["id"] for item in list_response.json()["data"]["items"]]

    assert agent_id not in ids
