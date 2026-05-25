"""Submission service: CRUD operations and validation logic."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundException, PermissionDeniedException
from app.models.submission import Submission
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionUpdate


class SubmissionService:
    """Service for submission management operations."""

    @staticmethod
    async def list_submissions(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        task_id: Optional[str] = None,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """List submissions with filters and pagination."""
        query = (
            select(Submission)
            .options(
                selectinload(Submission.student),
                selectinload(Submission.task),
                selectinload(Submission.evaluations),
            )
        )
        count_base = select(func.count()).select_from(Submission)

        if task_id:
            query = query.where(Submission.task_id == task_id)
            count_base = count_base.where(Submission.task_id == task_id)
        if student_id:
            query = query.where(Submission.student_id == student_id)
            count_base = count_base.where(Submission.student_id == student_id)
        if status:
            query = query.where(Submission.status == status)
            count_base = count_base.where(Submission.status == status)

        total_result = await db.execute(count_base)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(Submission.submitted_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        submissions = result.unique().scalars().all()

        items = [_format_submission_item(sub) for sub in submissions]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def get_submission(db: AsyncSession, submission_id: str) -> Submission:
        """Get a submission by ID with all relationships."""
        result = await db.execute(
            select(Submission)
            .options(
                selectinload(Submission.student),
                selectinload(Submission.task).selectinload(Task.project),
                selectinload(Submission.evaluations),
            )
            .where(Submission.id == submission_id)
        )
        submission = result.unique().scalar_one_or_none()
        if submission is None:
            raise ResourceNotFoundException("提交记录不存在")
        return submission

    @staticmethod
    async def update_submission(
        db: AsyncSession, submission_id: str, data: SubmissionUpdate, user: User
    ) -> Submission:
        """Update a submission (resubmit content)."""
        submission = await SubmissionService.get_submission(db, submission_id)

        # Only the submitting student can update their own submission
        if submission.student_id != user.id and user.role not in ("teacher", "system_admin"):
            raise PermissionDeniedException("只能修改自己的提交")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(submission, key, value)

        db.add(submission)
        await db.flush()
        await db.refresh(submission)
        return submission


def _format_submission_item(submission: Submission) -> dict:
    """Format a submission model instance into a response dict."""
    try:
        task_title = submission.task.title if submission.task else None
    except Exception:
        task_title = None

    try:
        student_name = submission.student.name if submission.student else None
    except Exception:
        student_name = None

    try:
        evaluation_count = len(submission.evaluations) if submission.evaluations else 0
    except Exception:
        evaluation_count = 0

    return {
        "id": submission.id,
        "task_id": submission.task_id,
        "task_title": task_title,
        "student_id": submission.student_id,
        "student_name": student_name,
        "group_name": submission.group_name,
        "content": submission.content,
        "attachments": submission.attachments,
        "status": submission.status,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "evaluation_count": evaluation_count,
        "created_at": submission.created_at.isoformat() if submission.created_at else None,
        "updated_at": submission.updated_at.isoformat() if submission.updated_at else None,
    }
