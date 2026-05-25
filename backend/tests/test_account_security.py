import time

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str, password: str = "password") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(client: TestClient) -> dict[str, str]:
    return _login(client, "admin", "admin123")


def _create_teacher(client: TestClient, username: str, password: str = "password") -> dict:
    admin_headers = _admin_headers(client)
    schools = client.get("/api/v1/org/schools", headers=admin_headers)
    assert schools.status_code == 200
    school_id = schools.json()["data"]["items"][0]["id"]
    response = client.post(
        "/api/v1/users",
        json={
            "username": username,
            "password": password,
            "name": "Password Test Teacher",
            "role": "teacher",
            "school_id": school_id,
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_user_can_change_own_password_and_old_password_stops_working():
    username = f"phase5_self_{int(time.time() * 1000)}"
    old_password = "password"
    new_password = "phase5-new-password"

    with TestClient(app) as client:
        _create_teacher(client, username, old_password)
        headers = _login(client, username, old_password)

        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": old_password, "new_password": new_password},
            headers=headers,
        )
        old_login = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": old_password},
        )
        new_login = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": new_password},
        )

    assert response.status_code == 200
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password():
    username = f"phase5_wrong_{int(time.time() * 1000)}"

    with TestClient(app) as client:
        _create_teacher(client, username, "password")
        headers = _login(client, username, "password")

        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "not-current", "new_password": "phase5-new-password"},
            headers=headers,
        )

    assert response.status_code == 400


def test_admin_can_reset_user_password_and_non_admin_cannot():
    username = f"phase5_reset_{int(time.time() * 1000)}"
    new_password = "phase5-reset-password"

    with TestClient(app) as client:
        user = _create_teacher(client, username, "password")
        teacher_headers = _login(client, username, "password")
        admin_headers = _admin_headers(client)

        forbidden = client.post(
            f"/api/v1/users/{user['id']}/reset-password",
            json={"new_password": "blocked-password"},
            headers=teacher_headers,
        )
        reset = client.post(
            f"/api/v1/users/{user['id']}/reset-password",
            json={"new_password": new_password},
            headers=admin_headers,
        )
        old_login = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "password"},
        )
        new_login = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": new_password},
        )

    assert forbidden.status_code == 403
    assert reset.status_code == 200
    assert old_login.status_code == 401
    assert new_login.status_code == 200
