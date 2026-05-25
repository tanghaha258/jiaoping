"""Project management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import ProjectService, _format_project_item

router = APIRouter(prefix="/projects")


@router.get("")
async def list_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    grade: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List projects with pagination and filters.

    Teachers see their own projects plus active/completed projects in their school.
    Admins see all projects in their school.
    Students see active/completed projects in their class/school.
    """
    result = await ProjectService.list_projects(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        grade=grade,
        current_user=current_user,
    )
    return success_response(data=result)


@router.post("")
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Create a new project. Teacher only."""
    project = await ProjectService.create_project(db=db, data=data, user=current_user)
    # Reload with relationships for response
    project_full = await ProjectService.get_project(db=db, project_id=project.id)
    return success_response(data=_format_project_item(project_full), message="项目创建成功")


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project details by ID."""
    project = await ProjectService.get_project(db=db, project_id=project_id)
    return success_response(data=_format_project_item(project))


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Update project information. Owner or admin only."""
    # Verify ownership
    project = await ProjectService.get_project(db=db, project_id=project_id)
    if project.owner_id != current_user.id and current_user.role != "system_admin":
        from app.core.exceptions import PermissionDeniedException
        raise PermissionDeniedException("只有项目创建者可以修改项目")

    project = await ProjectService.update_project(db=db, project_id=project_id, data=data)
    project_full = await ProjectService.get_project(db=db, project_id=project.id)
    return success_response(data=_format_project_item(project_full), message="项目更新成功")


@router.post("/{project_id}/activate")
async def activate_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Transition project from draft to active."""
    project = await ProjectService.activate_project(db=db, project_id=project_id)
    project_full = await ProjectService.get_project(db=db, project_id=project.id)
    return success_response(data=_format_project_item(project_full), message="项目已发布")


@router.post("/{project_id}/complete")
async def complete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Transition project from active to completed."""
    project = await ProjectService.complete_project(db=db, project_id=project_id)
    project_full = await ProjectService.get_project(db=db, project_id=project.id)
    return success_response(data=_format_project_item(project_full), message="项目已完成")


@router.post("/{project_id}/archive")
async def archive_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Transition project from completed to archived."""
    project = await ProjectService.archive_project(db=db, project_id=project_id)
    project_full = await ProjectService.get_project(db=db, project_id=project.id)
    return success_response(data=_format_project_item(project_full), message="项目已归档")
