import time

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, username: str, password: str = "password") -> dict[str, str]:
    if username == "admin":
        password = "admin123"
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _package(suffix: str) -> dict:
    return {
        "regions": [{"name": f"Phase 6 Region {suffix}", "code": f"p6-region-{suffix}"}],
        "schools": [
            {
                "region_code": f"p6-region-{suffix}",
                "name": f"Phase 6 School {suffix}",
                "code": f"p6-school-{suffix}",
                "status": "active",
            }
        ],
        "classes": [
            {
                "school_code": f"p6-school-{suffix}",
                "grade": "grade_7",
                "name": f"Phase 6 Class {suffix}",
                "academic_year": "2026-2027",
            }
        ],
        "subjects": [{"name": f"Phase 6 Subject {suffix}", "stage": "junior_high"}],
    }


def test_admin_can_template_export_dry_run_and_import_org_data_package():
    suffix = str(int(time.time() * 1000))

    with TestClient(app) as client:
        headers = _login(client, "admin")
        package = _package(suffix)

        template_response = client.get("/api/v1/org/data/template", headers=headers)
        export_response = client.get("/api/v1/org/data/export", headers=headers)
        dry_run_response = client.post(
            "/api/v1/org/data/import",
            json={"dry_run": True, "package": package},
            headers=headers,
        )
        missing_after_dry_run = client.get(
            "/api/v1/org/regions",
            params={"keyword": f"p6-region-{suffix}"},
            headers=headers,
        )
        import_response = client.post(
            "/api/v1/org/data/import",
            json={"dry_run": False, "package": package},
            headers=headers,
        )
        repeat_response = client.post(
            "/api/v1/org/data/import",
            json={"dry_run": False, "package": package},
            headers=headers,
        )
        created_region = client.get(
            "/api/v1/org/regions",
            params={"keyword": f"p6-region-{suffix}"},
            headers=headers,
        )

    assert template_response.status_code == 200
    template = template_response.json()["data"]
    assert {"regions", "schools", "classes", "subjects"} <= set(template.keys())
    assert template["schools"][0]["region_code"] == template["regions"][0]["code"]

    assert export_response.status_code == 200
    exported = export_response.json()["data"]
    assert len(exported["regions"]) >= 1
    assert len(exported["schools"]) >= 1

    assert dry_run_response.status_code == 200
    dry_run = dry_run_response.json()["data"]
    assert dry_run["dry_run"] is True
    assert dry_run["created"]["regions"] == 1
    assert dry_run["created"]["schools"] == 1
    assert dry_run["created"]["classes"] == 1
    assert dry_run["created"]["subjects"] == 1
    assert missing_after_dry_run.json()["data"]["total"] == 0

    assert import_response.status_code == 200
    imported = import_response.json()["data"]
    assert imported["dry_run"] is False
    assert imported["created"]["regions"] == 1
    assert imported["created"]["schools"] == 1
    assert imported["created"]["classes"] == 1
    assert imported["created"]["subjects"] == 1
    assert created_region.json()["data"]["total"] == 1

    assert repeat_response.status_code == 200
    repeated = repeat_response.json()["data"]
    assert repeated["created"]["regions"] == 0
    assert repeated["skipped"]["regions"] == 1
    assert repeated["skipped"]["schools"] == 1
    assert repeated["skipped"]["classes"] == 1
    assert repeated["skipped"]["subjects"] == 1


def test_non_admin_cannot_import_or_export_org_data_package():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")

        export_response = client.get("/api/v1/org/data/export", headers=teacher_headers)
        import_response = client.post(
            "/api/v1/org/data/import",
            json={"dry_run": True, "package": _package("forbidden")},
            headers=teacher_headers,
        )

    assert export_response.status_code == 403
    assert import_response.status_code == 403
