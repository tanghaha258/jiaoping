"""API v1 main router - includes all sub-routers."""

from fastapi import APIRouter

from app.api.routers.health import router as health_router
from app.api.routers.auth import router as auth_router
from app.api.routers.users import router as users_router
from app.api.routers.ai import router as ai_router
from app.api.routers.audit_logs import router as audit_logs_router
from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.projects import router as projects_router
from app.api.routers.tasks import router as tasks_router
from app.api.routers.submissions import router as submissions_router
from app.api.routers.rubrics import router as rubrics_router
from app.api.routers.evaluations import router as evaluations_router
from app.api.routers.resources import router as resources_router
from app.api.routers.student import router as student_router
from app.api.routers.org import router as org_router
from app.api.routers.settings import router as settings_router

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(ai_router, tags=["AI 智能体"])
api_router.include_router(audit_logs_router, tags=["audit logs"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(tasks_router, tags=["tasks"])
api_router.include_router(submissions_router, tags=["submissions"])
api_router.include_router(rubrics_router, tags=["rubrics"])
api_router.include_router(evaluations_router, tags=["evaluations"])
api_router.include_router(resources_router, tags=["resources"])
api_router.include_router(student_router, tags=["student"])
api_router.include_router(org_router, tags=["organization"])
api_router.include_router(settings_router, tags=["settings"])
