"""Health check endpoints for process liveness and deployment readiness."""

from pathlib import Path
import tempfile

from fastapi import APIRouter
from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.response import success_response
from app.db.session import AsyncSessionFactory
from app.models.ai_agent import AIAgent
from app.models.class_ import Class
from app.models.school import School
from app.models.subject import Subject
from app.models.user import User

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return service health status."""
    return success_response(
        data={
            "status": "ok",
            "service": "zhikua-xueping-api",
            "version": "0.1.0",
            "environment": settings.APP_ENV,
        },
        message="Service is healthy",
    )


@router.get("/health/ready")
async def readiness_check():
    """Return deployment readiness checks for operators and smoke tests."""
    checks = {
        "database": await _check_database(),
        "uploads": _check_uploads(),
        "seed_data": await _check_seed_data(),
    }
    ready = all(check["status"] == "ok" for check in checks.values())

    return success_response(
        data={
            "status": "ready" if ready else "degraded",
            "checks": checks,
            "ai_provider": _ai_provider_status(),
        },
        message="Service is ready" if ready else "Service is degraded",
    )


async def _check_database() -> dict:
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - exercised only by broken deployments
        return {"status": "error", "message": str(exc)}


def _check_uploads() -> dict:
    try:
        upload_dir = Path(settings.UPLOAD_DIR).resolve()
        upload_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".readiness-", dir=upload_dir, delete=True):
            pass
        return {"status": "ok", "path": str(upload_dir)}
    except Exception as exc:  # pragma: no cover - exercised only by broken deployments
        return {"status": "error", "message": str(exc), "path": str(Path(settings.UPLOAD_DIR))}


async def _check_seed_data() -> dict:
    try:
        async with AsyncSessionFactory() as session:
            counts = {
                "users": await _count(session, User),
                "schools": await _count(session, School),
                "classes": await _count(session, Class),
                "subjects": await _count(session, Subject),
                "ai_agents": await _count(session, AIAgent),
            }
        status = "ok" if all(value > 0 for value in counts.values()) else "missing"
        return {"status": status, "counts": counts}
    except Exception as exc:  # pragma: no cover - exercised only by broken deployments
        return {"status": "error", "message": str(exc), "counts": {}}


async def _count(session, model) -> int:
    result = await session.execute(select(func.count(model.id)))
    return int(result.scalar_one())


def _ai_provider_status() -> dict:
    gjt_configured = all(
        [
            settings.GJT_API_BASE_URL,
            settings.GJT_API_KEY,
            settings.GJT_AGENT_ID,
        ]
    )
    return {
        "mode": "gjt_api" if gjt_configured else "mock",
        "gjt_configured": bool(gjt_configured),
        "timeout_seconds": settings.GJT_API_TIMEOUT_SECONDS,
    }
