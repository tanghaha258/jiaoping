"""Task management endpoints."""

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService, _format_task_item
from app.services.submission_service import _format_submission_item

router = APIRouter()


# ─── Task CRUD (scoped under projects) ──────────────────────────────────────────

@router.get("/projects/{project_id}/tasks")
async def list_tasks(
    project_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks for a specific project."""
    result = await TaskService.list_tasks(
        db=db,
        project_id=project_id,
        page=page,
        page_size=page_size,
        status=status,
    )
    return success_response(data=result)


@router.post("/projects/{project_id}/tasks")
async def create_task(
    project_id: str,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Create a new task within a project. Teacher only."""
    task = await TaskService.create_task(db=db, project_id=project_id, data=data)
    task_full = await TaskService.get_task(db=db, task_id=task.id)
    return success_response(data=_format_task_item(task_full), message="任务创建成功")


# ─── Task detail & mutation (plain /tasks/{id}) ─────────────────────────────────

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get task details by ID."""
    task = await TaskService.get_task(db=db, task_id=task_id)
    return success_response(data=_format_task_item(task))


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Update a task. Only draft tasks can be updated. Teacher only."""
    task = await TaskService.update_task(db=db, task_id=task_id, data=data)
    task_full = await TaskService.get_task(db=db, task_id=task.id)
    return success_response(data=_format_task_item(task_full), message="任务更新成功")


@router.post("/tasks/{task_id}/publish")
async def publish_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Publish a draft task so students can see and submit. Teacher only."""
    task = await TaskService.publish_task(db=db, task_id=task_id)
    task_full = await TaskService.get_task(db=db, task_id=task.id)
    return success_response(data=_format_task_item(task_full), message="任务已发布")


@router.post("/tasks/{task_id}/close")
async def close_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Close a published task to stop receiving submissions. Teacher only."""
    task = await TaskService.close_task(db=db, task_id=task_id)
    task_full = await TaskService.get_task(db=db, task_id=task.id)
    return success_response(data=_format_task_item(task_full), message="任务已关闭")


# ─── Submissions under a task ───────────────────────────────────────────────────

@router.post("/tasks/{task_id}/submissions")
async def submit_to_task(
    task_id: str,
    content: str = Body(None),
    group_name: str = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    """Student submits work to a task.

    Validates: task is published, student is in the project's class.
    """
    submission = await TaskService.submit_to_task(
        db=db,
        task_id=task_id,
        content=content,
        group_name=group_name,
        attachments=None,
        student=current_user,
    )
    return success_response(data=_format_submission_item(submission), message="提交成功")


@router.get("/tasks/{task_id}/submissions")
async def list_task_submissions(
    task_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """List submissions for a task. Teacher only."""
    result = await TaskService.list_task_submissions(
        db=db,
        task_id=task_id,
        page=page,
        page_size=page_size,
        status=status,
    )
    return success_response(data=result)
