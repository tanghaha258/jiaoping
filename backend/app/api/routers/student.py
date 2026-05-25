"""Student-specific endpoints for tasks and submissions."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.services.student_service import StudentService

router = APIRouter(prefix="/student")


@router.get("/tasks")
async def list_student_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    """List tasks assigned to the current student (via their class)."""
    result = await StudentService.list_student_tasks(
        db=db,
        student=current_user,
        page=page,
        page_size=page_size,
        status=status,
    )
    return success_response(data=result)


@router.get("/submissions")
async def list_student_submissions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("student")),
):
    """List the current student's own submissions."""
    result = await StudentService.list_student_submissions(
        db=db,
        student=current_user,
        page=page,
        page_size=page_size,
    )
    return success_response(data=result)
