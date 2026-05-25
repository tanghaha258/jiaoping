from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[2]


def _login(client: TestClient, username: str) -> dict[str, str]:
    password = "admin123" if username == "admin" else "password"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_system_admin_can_view_trial_readiness_checklist():
    with TestClient(app) as client:
        admin_headers = _login(client, "admin")

        response = client.get(
            "/api/v1/dashboard/trial-readiness",
            headers=admin_headers,
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] in {"ready", "action_required"}
    assert set(data["summary"].keys()) == {"ok", "warning", "error"}
    assert isinstance(data["checked_at"], str)

    items = data["items"]
    assert items
    item_keys = {item["key"] for item in items}
    assert {
        "service_readiness",
        "organization_data",
        "user_accounts",
        "ai_contract",
        "teaching_workflow",
        "student_task_availability",
        "resources",
        "backup_path",
    }.issubset(item_keys)

    for item in items:
        assert set(item.keys()) == {
            "key",
            "label",
            "status",
            "description",
            "metric",
            "action",
            "route",
        }
        assert item["status"] in {"ok", "warning", "error"}
        assert item["label"]
        assert item["description"]


def test_school_admin_can_view_trial_readiness_checklist():
    with TestClient(app) as client:
        school_admin_headers = _login(client, "schooladmin")

        response = client.get(
            "/api/v1/dashboard/trial-readiness",
            headers=school_admin_headers,
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] in {"ready", "action_required"}
    assert len(data["items"]) >= 8


def test_non_admin_cannot_view_trial_readiness_checklist():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")

        response = client.get(
            "/api/v1/dashboard/trial-readiness",
            headers=teacher_headers,
        )

    assert response.status_code == 403
    assert response.json()["code"] == 403001


def test_backup_restore_artifacts_are_documented():
    backup_script = ROOT / "scripts" / "backup-sqlite.ps1"
    restore_script = ROOT / "scripts" / "restore-sqlite.ps1"
    deployment_doc = ROOT / "docs" / "DEPLOYMENT.md"

    assert backup_script.exists(), "Missing SQLite backup script"
    assert restore_script.exists(), "Missing SQLite restore script"

    backup_content = backup_script.read_text(encoding="utf-8")
    assert "Copy-Item" in backup_content
    assert "BackupDir" in backup_content

    restore_content = restore_script.read_text(encoding="utf-8")
    assert "SkipSafetyBackup" in restore_content
    assert "pre-restore" in restore_content
    assert "Copy-Item" in restore_content

    deployment_content = deployment_doc.read_text(encoding="utf-8")
    assert "SQLite Backup" in deployment_content
    assert "SQLite Restore" in deployment_content
