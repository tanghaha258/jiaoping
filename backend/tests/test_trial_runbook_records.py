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


def test_admin_can_create_and_list_trial_runbook_record():
    with TestClient(app) as client:
        headers = _login(client, "admin")
        payload = {
            "status": "checked",
            "note": "Provider mock rehearsal is ready for the trial handover.",
            "evidence": ["AI Provider: mock (normal)", "Recent diagnostics: no blocking item"],
        }

        create_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/ai_provider_rehearsal/records",
            headers=headers,
            json=payload,
        )
        list_response = client.get(
            "/api/v1/dashboard/trial-operations/records"
            "?stage_key=ai_provider_rehearsal&page=1&page_size=5",
            headers=headers,
        )
        audit_response = client.get(
            "/api/v1/audit-logs?action=trial_runbook.record&target_type=trial_runbook_stage",
            headers=headers,
        )

    assert create_response.status_code == 200, create_response.text
    created = create_response.json()["data"]
    assert created["stage_key"] == "ai_provider_rehearsal"
    assert created["status"] == payload["status"]
    assert created["note"] == payload["note"]
    assert created["evidence"] == payload["evidence"]
    assert created["operator_id"]
    assert created["operator_name"]
    assert created["created_at"]

    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()["data"]
    assert listed["total"] >= 1
    assert listed["page"] == 1
    assert listed["page_size"] == 5
    assert any(item["id"] == created["id"] for item in listed["items"])

    assert audit_response.status_code == 200, audit_response.text
    audit_items = audit_response.json()["data"]["items"]
    matching_logs = [
        item for item in audit_items
        if item["target_id"] == "ai_provider_rehearsal"
        and item["detail"]["status"] == "checked"
    ]
    assert matching_logs


def test_school_admin_can_create_records_and_teacher_is_blocked():
    with TestClient(app) as client:
        school_admin_headers = _login(client, "schooladmin")
        teacher_headers = _login(client, "teacher001")

        school_admin_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=school_admin_headers,
            json={
                "status": "blocked",
                "note": "Upload directory check needs site confirmation.",
                "evidence": ["Service readiness: warning"],
            },
        )
        teacher_post_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=teacher_headers,
            json={"status": "checked", "note": "teacher should not write", "evidence": []},
        )
        teacher_list_response = client.get(
            "/api/v1/dashboard/trial-operations/records",
            headers=teacher_headers,
        )

    assert school_admin_response.status_code == 200, school_admin_response.text
    assert teacher_post_response.status_code == 403
    assert teacher_post_response.json()["code"] == 403001
    assert teacher_list_response.status_code == 403
    assert teacher_list_response.json()["code"] == 403001


def test_trial_runbook_records_validate_stage_status_and_note_length():
    with TestClient(app) as client:
        headers = _login(client, "admin")

        invalid_stage_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/unknown_stage/records",
            headers=headers,
            json={"status": "checked", "note": "bad stage", "evidence": []},
        )
        invalid_status_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=headers,
            json={"status": "done", "note": "bad status", "evidence": []},
        )
        long_note_response = client.post(
            "/api/v1/dashboard/trial-operations/stages/service_readiness/records",
            headers=headers,
            json={"status": "checked", "note": "x" * 501, "evidence": []},
        )

    assert invalid_stage_response.status_code == 400
    assert invalid_status_response.status_code == 422
    assert long_note_response.status_code == 422
