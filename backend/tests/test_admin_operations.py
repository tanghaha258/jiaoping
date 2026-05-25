import time

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str) -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_system_admin_can_manage_org_data_and_settings():
    with TestClient(app) as client:
        admin_headers = _login(client, "admin")
        suffix = str(int(time.time() * 1000))

        region_response = client.post(
            "/api/v1/org/regions",
            json={"name": f"Phase 3 Region {suffix}", "code": f"PHASE3-REGION-{suffix}"},
            headers=admin_headers,
        )
        assert region_response.status_code == 200
        region = region_response.json()["data"]

        school_response = client.post(
            "/api/v1/org/schools",
            json={
                "region_id": region["id"],
                "name": f"Phase 3 School {suffix}",
                "code": f"PHASE3-SCHOOL-{suffix}",
                "status": "active",
            },
            headers=admin_headers,
        )
        assert school_response.status_code == 200
        school = school_response.json()["data"]

        class_response = client.post(
            "/api/v1/org/classes",
            json={
                "school_id": school["id"],
                "grade": "grade_7",
                "name": f"Phase 3 Class {suffix}",
                "academic_year": "2026-2027",
            },
            headers=admin_headers,
        )
        assert class_response.status_code == 200
        class_item = class_response.json()["data"]

        subject_response = client.post(
            "/api/v1/org/subjects",
            json={"name": f"Phase 3 Subject {suffix}", "stage": "junior_high"},
            headers=admin_headers,
        )
        assert subject_response.status_code == 200
        subject = subject_response.json()["data"]

        listed_schools = client.get(
            "/api/v1/org/schools",
            params={"keyword": suffix},
            headers=admin_headers,
        )
        assert listed_schools.status_code == 200
        listed_school_ids = {item["id"] for item in listed_schools.json()["data"]["items"]}
        assert school["id"] in listed_school_ids

        update_class = client.patch(
            f"/api/v1/org/classes/{class_item['id']}",
            json={"name": "Phase 3 Class Updated"},
            headers=admin_headers,
        )
        assert update_class.status_code == 200
        assert update_class.json()["data"]["name"] == "Phase 3 Class Updated"

        update_subject = client.patch(
            f"/api/v1/org/subjects/{subject['id']}",
            json={"stage": "junior_high_plus"},
            headers=admin_headers,
        )
        assert update_subject.status_code == 200
        assert update_subject.json()["data"]["stage"] == "junior_high_plus"

        setting_response = client.put(
            "/api/v1/settings/phase3.admin",
            json={
                "value": {"enabled": True, "note": "admin operations", "suffix": suffix},
                "description": "Phase 3 admin setting",
            },
            headers=admin_headers,
        )
        assert setting_response.status_code == 200
        assert setting_response.json()["data"]["value"]["enabled"] is True

        settings_list = client.get("/api/v1/settings", headers=admin_headers)
        assert settings_list.status_code == 200
        setting_keys = {item["key"] for item in settings_list.json()["data"]["items"]}
        assert "phase3.admin" in setting_keys


def test_system_admin_can_create_update_and_disable_users():
    with TestClient(app) as client:
        admin_headers = _login(client, "admin")
        schools = client.get("/api/v1/org/schools", headers=admin_headers)
        assert schools.status_code == 200
        school_id = schools.json()["data"]["items"][0]["id"]

        unique_username = f"phase3_user_{int(time.time() * 1000)}"

        create_response = client.post(
            "/api/v1/users",
            json={
                "username": unique_username,
                "password": "password",
                "name": "Phase 3 User",
                "role": "teacher",
                "school_id": school_id,
            },
            headers=admin_headers,
        )
        assert create_response.status_code == 200
        user = create_response.json()["data"]

        update_response = client.patch(
            f"/api/v1/users/{user['id']}",
            json={"name": "Phase 3 User Updated"},
            headers=admin_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["name"] == "Phase 3 User Updated"

        status_response = client.patch(
            f"/api/v1/users/{user['id']}/status",
            json={"status": "disabled"},
            headers=admin_headers,
        )
        assert status_response.status_code == 200
        assert status_response.json()["data"]["status"] == "disabled"


def test_non_admin_cannot_manage_org_or_settings():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")
        student_headers = _login(client, "student001")

        create_region = client.post(
            "/api/v1/org/regions",
            json={"name": "Forbidden Region", "code": "FORBIDDEN-REGION"},
            headers=teacher_headers,
        )
        assert create_region.status_code == 403
        assert create_region.json()["code"] == 403001

        list_settings = client.get("/api/v1/settings", headers=student_headers)
        assert list_settings.status_code == 403
        assert list_settings.json()["code"] == 403001
