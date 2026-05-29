"""Dashboard API endpoints — aggregate statistics for administrators and teachers."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import error_response, success_response
from app.models.user import User
from app.schemas.trial_runbook import TrialRunbookRecordCreate
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard")


def _resolve_scope(current_user: User) -> tuple[Optional[str], Optional[str]]:
    """Resolve scoping parameters based on the current user's role.

    Returns:
        (school_id, owner_id) tuple.
        - system_admin: no scope (both None) -- sees all data
        - school_admin: scoped to own school_id
        - teacher: scoped to own projects (via owner_id)
        - student: minimal scope (own school for general stats)
    """
    if current_user.role == "system_admin":
        return None, None
    if current_user.role == "school_admin":
        return current_user.school_id, None
    if current_user.role == "teacher":
        return None, current_user.id
    # student or other: show only their school's aggregate
    return current_user.school_id, None


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard overview with aggregate counts.

    Scope rules:
    - system_admin: all data across the platform
    - school_admin: data scoped to own school
    - teacher: project and task stats scoped to own projects
    - student: school-level aggregate only
    """
    school_id, owner_id = _resolve_scope(current_user)
    data = await DashboardService.get_overview(
        db=db,
        school_id=school_id,
        owner_id=owner_id,
    )
    return success_response(data=data, message="获取概览数据成功")


@router.get("/ai-usage")
async def get_ai_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI usage breakdown: calls by scenario and by provider.

    Scope rules:
    - system_admin: all data across the platform
    - school_admin: data scoped to own school
    - teacher: own AI calls
    - student: school-level aggregate only
    """
    school_id, owner_id = _resolve_scope(current_user)
    data = await DashboardService.get_ai_usage(
        db=db,
        school_id=school_id,
        owner_id=owner_id,
    )
    return success_response(data=data, message="获取AI使用数据成功")


@router.get("/trial-readiness")
async def get_trial_readiness(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Get the operational checklist for local trial readiness."""
    data = await DashboardService.get_trial_readiness(db=db)
    return success_response(data=data, message="试运行检查完成")


@router.get("/trial-operations/runbook")
async def get_trial_operations_runbook(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Get the stage-by-stage operations runbook for local trial rehearsal."""
    data = await DashboardService.get_trial_operations_runbook(db=db)
    return success_response(data=data, message="试运行演练台已生成")


@router.post("/trial-operations/stages/{stage_key}/records")
async def create_trial_runbook_record(
    stage_key: str,
    payload: TrialRunbookRecordCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Append one rehearsal evidence record for a trial operations stage."""
    try:
        data = await DashboardService.create_trial_runbook_record(
            db=db,
            user=current_user,
            stage_key=stage_key,
            payload=payload,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content=error_response(400001, str(exc)))
    except RuntimeError as exc:
        return JSONResponse(status_code=500, content=error_response(500001, str(exc)))
    return success_response(data=data, message="Trial runbook record saved")


@router.get("/trial-operations/records")
async def list_trial_runbook_records(
    stage_key: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """List recent rehearsal evidence records for the trial operations runbook."""
    try:
        data = await DashboardService.list_trial_runbook_records(
            db=db,
            user=current_user,
            stage_key=stage_key,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        return JSONResponse(status_code=400, content=error_response(400001, str(exc)))
    return success_response(data=data, message="Trial runbook records loaded")


@router.get("/trial-delivery/package")
async def get_trial_delivery_package(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin", "region_admin")),
):
    """Get the read-only onsite trial delivery package."""
    data = await DashboardService.get_trial_delivery_package(db=db, user=current_user)
    return success_response(data=data, message="Trial delivery package generated")


@router.get("/project-trends")
async def get_project_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project trends: counts by month and by status.

    Scope rules:
    - system_admin: all data across the platform
    - school_admin: data scoped to own school
    - teacher: own projects
    - student: school-level aggregate only
    """
    school_id, owner_id = _resolve_scope(current_user)
    data = await DashboardService.get_project_trends(
        db=db,
        school_id=school_id,
        owner_id=owner_id,
    )
    return success_response(data=data, message="获取项目趋势数据成功")
