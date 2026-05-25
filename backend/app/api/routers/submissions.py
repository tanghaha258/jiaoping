"""Submission management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.submission import SubmissionUpdate
from app.services.submission_service import SubmissionService, _format_submission_item

router = APIRouter(prefix="/submissions")


@router.get("")
async def list_submissions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    task_id: str = Query(default=None),
    student_id: str = Query(default=None),
    status: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List submissions with optional filters.

    Teachers see submissions in their school. Students see only their own.
    """
    # If student, force student_id to their own
    if current_user.role == "student":
        student_id = current_user.id

    result = await SubmissionService.list_submissions(
        db=db,
        page=page,
        page_size=page_size,
        task_id=task_id,
        student_id=student_id,
        status=status,
    )
    return success_response(data=result)


@router.get("/{submission_id}")
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get submission details by ID."""
    submission = await SubmissionService.get_submission(
        db=db,
        submission_id=submission_id,
        current_user=current_user,
    )
    return success_response(data=_format_submission_item(submission))


@router.patch("/{submission_id}")
async def update_submission(
    submission_id: str,
    data: SubmissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update/resubmit a submission."""
    submission = await SubmissionService.update_submission(
        db=db, submission_id=submission_id, data=data, user=current_user
    )
    sub_full = await SubmissionService.get_submission(db=db, submission_id=submission.id)
    return success_response(data=_format_submission_item(sub_full), message="提交已更新")
