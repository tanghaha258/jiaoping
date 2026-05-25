from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[2]


def test_health_endpoint_exposes_runtime_identity():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ok"
    assert data["service"] == "zhikua-xueping-api"
    assert data["version"] == "0.1.0"
    assert data["environment"] in {"development", "test", "production"}


def test_readiness_endpoint_checks_database_uploads_seed_data_and_ai_provider():
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ready"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["uploads"]["status"] == "ok"
    assert data["checks"]["seed_data"]["status"] == "ok"
    assert data["checks"]["seed_data"]["counts"]["users"] >= 1
    assert data["checks"]["seed_data"]["counts"]["ai_agents"] >= 1
    assert data["ai_provider"]["mode"] in {"mock", "gjt_api"}
    assert isinstance(data["ai_provider"]["gjt_configured"], bool)


def test_deployment_artifacts_document_operational_runtime():
    required_files = [
        ROOT / "backend" / ".env.example",
        ROOT / "frontend" / ".env.example",
        ROOT / "scripts" / "start-local.ps1",
        ROOT / "scripts" / "check-release.ps1",
        ROOT / "scripts" / "smoke_deploy.py",
        ROOT / "docs" / "DEPLOYMENT.md",
    ]

    for path in required_files:
        assert path.exists(), f"Missing deployment artifact: {path}"

    backend_env = (ROOT / "backend" / ".env.example").read_text(encoding="utf-8")
    for key in [
        "APP_ENV",
        "DATABASE_URL",
        "JWT_SECRET",
        "UPLOAD_DIR",
        "GJT_API_BASE_URL",
        "GJT_API_KEY",
        "GJT_AGENT_ID",
    ]:
        assert key in backend_env

    smoke_script = (ROOT / "scripts" / "smoke_deploy.py").read_text(encoding="utf-8")
    assert "JIAOPING_API_BASE" in smoke_script
    assert "/health/ready" in smoke_script
    assert "/ai/contracts" in smoke_script

    deployment_doc = (ROOT / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8")
    assert "Local Trial" in deployment_doc
    assert "Docker Trial" in deployment_doc
    assert "Smoke Test" in deployment_doc
