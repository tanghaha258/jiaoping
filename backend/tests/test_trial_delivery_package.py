from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str) -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_admin_can_view_trial_delivery_package():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        response = client.get("/api/v1/dashboard/trial-delivery/package", headers=headers)

    assert response.status_code == 200, response.text
    package = response.json()["data"]

    assert package["status"] in {"ready", "action_required"}
    assert package["generated_at"]
    assert package["summary"]["readiness_ok"] >= 0
    assert package["summary"]["readiness_warning"] >= 0
    assert package["summary"]["readiness_error"] >= 0
    assert package["summary"]["runbook_checked"] >= 0
    assert package["summary"]["runbook_blocked"] >= 0
    assert package["summary"]["runbook_skipped"] >= 0

    checklist_keys = {item["key"] for item in package["acceptance_checklist"]}
    assert checklist_keys == {
        "service_readiness",
        "base_data",
        "account_access",
        "ai_provider_rehearsal",
        "teaching_workflow",
        "resource_and_backup",
    }
    for item in package["acceptance_checklist"]:
        assert item["title"]
        assert item["status"] in {"ok", "warning", "error"}
        assert item["route"]
        assert isinstance(item["evidence"], list)
        assert "latest_record" in item

    assert any(step["route"] == "/teacher/projects" for step in package["demo_script"])
    assert any(step["route"] == "/student/tasks" for step in package["demo_script"])
    assert any(step["route"] == "/admin/ai-calls" for step in package["demo_script"])

    account_usernames = {item["username"] for item in package["accounts"]}
    assert {"admin", "schooladmin", "teacher001", "student001"}.issubset(account_usernames)
    for account in package["accounts"]:
        assert "password_hash" not in account
        assert "password" not in account
        assert account["password_hint"]
        assert "正式试点前必须重置" in account["password_hint"]

    assert package["materials"]["markdown"].startswith("# 试点交付包")
    assert "现场验收清单" in package["materials"]["markdown"]
    assert "演示脚本" in package["materials"]["markdown"]
    assert "测试账号交付" in package["materials"]["markdown"]
    assert '"acceptance_checklist"' in package["materials"]["json"]


def test_school_admin_can_view_delivery_package_and_teacher_is_blocked():
    with TestClient(app) as client:
        school_admin_headers = _login(client, "schooladmin")
        teacher_headers = _login(client, "teacher001")

        school_admin_response = client.get(
            "/api/v1/dashboard/trial-delivery/package",
            headers=school_admin_headers,
        )
        teacher_response = client.get(
            "/api/v1/dashboard/trial-delivery/package",
            headers=teacher_headers,
        )

    assert school_admin_response.status_code == 200, school_admin_response.text
    assert teacher_response.status_code == 403
    assert teacher_response.json()["code"] == 403001


def test_blocked_runbook_record_marks_delivery_package_action_required():
    note = "P12 delivery package blocked evidence marker"
    with TestClient(app) as client:
        headers = _login(client, "admin")
        record_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/ai_provider_rehearsal/records",
            headers=headers,
            json={
                "status": "blocked",
                "note": note,
                "evidence": ["Provider rehearsal blocked for package test"],
            },
        )
        package_response = client.get(
            "/api/v1/dashboard/trial-delivery/package",
            headers=headers,
        )

    assert record_response.status_code == 200, record_response.text
    assert package_response.status_code == 200, package_response.text
    package = package_response.json()["data"]
    provider_item = next(
        item for item in package["acceptance_checklist"]
        if item["key"] == "ai_provider_rehearsal"
    )
    assert package["status"] == "action_required"
    assert package["summary"]["runbook_blocked"] >= 1
    assert provider_item["latest_record"]["status"] == "blocked"
    assert provider_item["latest_record"]["note"] == note
    assert "Provider rehearsal blocked for package test" in package["materials"]["markdown"]
