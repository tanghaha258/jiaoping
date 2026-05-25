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


def _org_package(suffix: str) -> dict:
    return {
        "regions": [{"name": f"Phase 7 Region {suffix}", "code": f"p7-region-{suffix}"}],
        "schools": [
            {
                "region_code": f"p7-region-{suffix}",
                "name": f"Phase 7 School {suffix}",
                "code": f"p7-school-{suffix}",
                "status": "active",
            }
        ],
        "classes": [
            {
                "school_code": f"p7-school-{suffix}",
                "grade": "grade_7",
                "name": f"Phase 7 Class {suffix}",
                "academic_year": "2026-2027",
            }
        ],
        "subjects": [],
    }


def _user_package(suffix: str) -> dict:
    return {
        "users": [
            {
                "username": f"p7_teacher_{suffix}",
                "name": "Phase 7 Teacher",
                "role": "teacher",
                "school_code": f"p7-school-{suffix}",
                "class": None,
                "initial_password": "phase7pass",
            },
            {
                "username": f"p7_student_{suffix}",
                "name": "Phase 7 Student",
                "role": "student",
                "school_code": f"p7-school-{suffix}",
                "class": {
                    "grade": "grade_7",
                    "name": f"Phase 7 Class {suffix}",
                    "academic_year": "2026-2027",
                },
                "initial_password": "phase7pass",
            },
        ]
    }


def test_admin_can_template_export_dry_run_and_import_user_package():
    suffix = str(int(time.time() * 1000))

    with TestClient(app) as client:
        headers = _login(client, "admin")
        org_import = client.post(
            "/api/v1/org/data/import",
            json={"dry_run": False, "package": _org_package(suffix)},
            headers=headers,
        )
        assert org_import.status_code == 200

        package = _user_package(suffix)
        template_response = client.get("/api/v1/users/data/template", headers=headers)
        export_response = client.get("/api/v1/users/data/export", headers=headers)
        dry_run_response = client.post(
            "/api/v1/users/data/import",
            json={"dry_run": True, "package": package},
            headers=headers,
        )
        missing_after_dry_run = client.get(
            "/api/v1/users",
            params={"keyword": f"p7_student_{suffix}"},
            headers=headers,
        )
        import_response = client.post(
            "/api/v1/users/data/import",
            json={"dry_run": False, "package": package},
            headers=headers,
        )
        repeat_response = client.post(
            "/api/v1/users/data/import",
            json={"dry_run": False, "package": package},
            headers=headers,
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": f"p7_student_{suffix}", "password": "phase7pass"},
        )
        imported_student = client.get(
            "/api/v1/users",
            params={"keyword": f"p7_student_{suffix}", "role": "student"},
            headers=headers,
        )

    assert template_response.status_code == 200
    template = template_response.json()["data"]
    assert "users" in template
    assert template["users"][1]["class"]["academic_year"]

    assert export_response.status_code == 200
    exported = export_response.json()["data"]
    assert len(exported["users"]) >= 1
    assert all("initial_password" not in item for item in exported["users"])

    assert dry_run_response.status_code == 200
    dry_run = dry_run_response.json()["data"]
    assert dry_run["dry_run"] is True
    assert dry_run["created"]["users"] == 2
    assert dry_run["skipped"]["users"] == 0
    assert dry_run["initial_passwords"] == []
    assert missing_after_dry_run.json()["data"]["total"] == 0

    assert import_response.status_code == 200
    imported = import_response.json()["data"]
    assert imported["dry_run"] is False
    assert imported["created"]["users"] == 2
    assert imported["skipped"]["users"] == 0
    assert {item["username"] for item in imported["initial_passwords"]} == {
        f"p7_teacher_{suffix}",
        f"p7_student_{suffix}",
    }

    assert repeat_response.status_code == 200
    repeated = repeat_response.json()["data"]
    assert repeated["created"]["users"] == 0
    assert repeated["skipped"]["users"] == 2
    assert repeated["initial_passwords"] == []

    assert login_response.status_code == 200
    students = imported_student.json()["data"]["items"]
    assert len(students) == 1
    assert students[0]["class_id"]


def test_user_import_reports_missing_class_without_creating_partial_rows():
    suffix = str(int(time.time() * 1000))

    with TestClient(app) as client:
        headers = _login(client, "admin")
        org_import = client.post(
            "/api/v1/org/data/import",
            json={"dry_run": False, "package": _org_package(suffix)},
            headers=headers,
        )
        assert org_import.status_code == 200

        package = _user_package(suffix)
        package["users"][1]["class"]["name"] = "Missing Class"
        response = client.post(
            "/api/v1/users/data/import",
            json={"dry_run": False, "package": package},
            headers=headers,
        )
        users = client.get(
            "/api/v1/users",
            params={"keyword": f"p7_student_{suffix}"},
            headers=headers,
        )

    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["created"]["users"] == 1
    assert len(summary["errors"]) == 1
    assert "Missing Class" in summary["errors"][0]
    assert users.json()["data"]["total"] == 0


def test_non_admin_cannot_import_or_export_user_package():
    with TestClient(app) as client:
        teacher_headers = _login(client, "teacher001")

        export_response = client.get("/api/v1/users/data/export", headers=teacher_headers)
        import_response = client.post(
            "/api/v1/users/data/import",
            json={"dry_run": True, "package": {"users": []}},
            headers=teacher_headers,
        )

    assert export_response.status_code == 403
    assert import_response.status_code == 403
