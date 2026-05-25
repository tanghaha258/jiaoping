"""Student-specific service: tasks and submissions scoped to the student."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.project import Project
from app.models.project_class import ProjectClass
from app.models.submission import Submission
from app.models.user import User
from app.services.task_service import _format_task_item
from app.services.submission_service import _format_submission_item


class StudentService:
    """Service for student-specific operations."""

    @staticmethod
    async def list_student_tasks(
        db: AsyncSession,
        student: User,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> dict:
        """List published tasks for the student's class."""
        # Get project IDs that include the student's class
        class_project_ids = (
            select(ProjectClass.project_id)
            .where(ProjectClass.class_id == student.class_id)
        )

        query = (
            select(Task)
            .options(
                selectinload(Task.rubric),
                selectinload(Task.submissions),
                selectinload(Task.project),
            )
            .where(
                Task.project_id.in_(class_project_ids),
                Task.status.in_(["published", "closed"]),
            )
        )
        count_base = (
            select(func.count())
            .select_from(Task)
            .where(
                Task.project_id.in_(class_project_ids),
                Task.status.in_(["published", "closed"]),
            )
        )

        if status:
            query = query.where(Task.status == status)
            count_base = count_base.where(Task.status == status)

        total_result = await db.execute(count_base)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        tasks = result.unique().scalars().all()

        task_ids = [task.id for task in tasks]
        submission_by_task = {}
        if task_ids:
            sub_result = await db.execute(
                select(Submission).where(
                    Submission.task_id.in_(task_ids),
                    Submission.student_id == student.id,
                )
            )
            for submission in sub_result.scalars().all():
                submission_by_task[submission.task_id] = submission

        items = []
        for task in tasks:
            item = _format_task_item(task)
            item["project_name"] = task.project.name if task.project else None
            submission = submission_by_task.get(task.id)
            item["submission_id"] = submission.id if submission else None
            item["submission_status"] = _student_submission_status(submission)
            items.append(item)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }


def _student_submission_status(submission: Submission | None) -> str:
    if submission is None:
        return "pending"
    if submission.status in ("reviewed", "returned"):
        return "reviewed"
    return "submitted"

    @staticmethod
    async def list_student_submissions(
        db: AsyncSession,
        student: User,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List the current student's own submissions."""
        query = (
            select(Submission)
            .options(
                selectinload(Submission.student),
                selectinload(Submission.task),
                selectinload(Submission.evaluations),
            )
            .where(Submission.student_id == student.id)
        )
        count_base = (
            select(func.count())
            .select_from(Submission)
            .where(Submission.student_id == student.id)
        )

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
