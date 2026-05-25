"""Task service: CRUD operations, state transitions, and submissions listing."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    InvalidStateTransitionException,
    ResourceNotFoundException,
)
from app.models.task import Task
from app.models.project import Project
from app.models.submission import Submission
from app.models.user import User
from app.models.rubric import Rubric
from app.schemas.task import TaskCreate, TaskUpdate


# Valid state transitions
TASK_TRANSITIONS = {
    "draft": "published",
    "published": "closed",
}


class TaskService:
    """Service for task management operations."""

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> dict:
        """List tasks for a project with pagination."""
        # Verify project exists
        proj_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        if proj_result.scalar_one_or_none() is None:
            raise ResourceNotFoundException("项目不存在")

        query = (
            select(Task)
            .options(
                selectinload(Task.rubric),
                selectinload(Task.submissions),
            )
            .where(Task.project_id == project_id)
        )
        count_base = (
            select(func.count()).select_from(Task).where(Task.project_id == project_id)
        )

        if status:
            query = query.where(Task.status == status)
            count_base = count_base.where(Task.status == status)

        # Count
        total_result = await db.execute(count_base)
        total = total_result.scalar()

        # Fetch page
        offset = (page - 1) * page_size
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        tasks = result.unique().scalars().all()

        items = [_format_task_item(task) for task in tasks]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def create_task(
        db: AsyncSession, project_id: str, data: TaskCreate
    ) -> Task:
        """Create a new task within a project."""
        # Verify project exists
        proj_result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        if proj_result.scalar_one_or_none() is None:
            raise ResourceNotFoundException("项目不存在")

        # Verify rubric if provided
        if data.rubric_id:
            rub_result = await db.execute(
                select(Rubric).where(Rubric.id == data.rubric_id)
            )
            if rub_result.scalar_one_or_none() is None:
                raise ResourceNotFoundException("量规不存在")

        task = Task(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=data.title,
            description=data.description,
            task_type=data.task_type,
            submit_type=data.submit_type,
            rubric_id=data.rubric_id,
            due_at=data.due_at,
            status="draft",
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        return task

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str) -> Task:
        """Get a task by ID with relationships."""
        result = await db.execute(
            select(Task)
            .options(
                selectinload(Task.rubric),
                selectinload(Task.submissions),
                selectinload(Task.project),
            )
            .where(Task.id == task_id)
        )
        task = result.unique().scalar_one_or_none()
        if task is None:
            raise ResourceNotFoundException("任务不存在")
        return task

    @staticmethod
    async def update_task(
        db: AsyncSession, task_id: str, data: TaskUpdate
    ) -> Task:
        """Update a task's fields."""
        task = await TaskService.get_task(db, task_id)

        # Only allow updates while in draft status
        if task.status != "draft":
            raise InvalidStateTransitionException("只有草稿状态的任务可以修改")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(task, key, value)

        db.add(task)
        await db.flush()
        await db.refresh(task)
        return task

    @staticmethod
    async def _transition_status(
        db: AsyncSession, task_id: str, transition_to: str
    ) -> Task:
        """Internal helper to perform a state transition."""
        task = await TaskService.get_task(db, task_id)

        current = task.status
        expected_next = TASK_TRANSITIONS.get(current)
        if expected_next != transition_to:
            raise InvalidStateTransitionException(
                f"任务状态不能从 '{current}' 转换到 '{transition_to}'"
            )

        task.status = transition_to
        db.add(task)
        await db.flush()
        await db.refresh(task)
        return task

    @staticmethod
    async def publish_task(db: AsyncSession, task_id: str) -> Task:
        """Publish a draft task for students to see."""
        return await TaskService._transition_status(db, task_id, "published")

    @staticmethod
    async def close_task(db: AsyncSession, task_id: str) -> Task:
        """Close a published task to stop receiving submissions."""
        return await TaskService._transition_status(db, task_id, "closed")

    @staticmethod
    async def submit_to_task(
        db: AsyncSession,
        task_id: str,
        content: Optional[str],
        group_name: Optional[str],
        attachments: Optional[list],
        student: User,
    ) -> Submission:
        """A student submits work to a task.

        Validates: task must be published, student must be in the project's class.
        """
        task = await TaskService.get_task(db, task_id)

        if task.status != "published":
            raise InvalidStateTransitionException("只有已发布的任务可以提交作业")

        # Validate the student belongs to one of the project's classes
        project = task.project
        if project is None:
            raise ResourceNotFoundException("关联的项目不存在")

        # Check if student is in any of the project's classes
        # Need to load project classes
        proj_result = await db.execute(
            select(Project)
            .options(selectinload(Project.classes))
            .where(Project.id == project.id)
        )
        project_full = proj_result.unique().scalar_one_or_none()

        valid_class_ids = [pc.class_id for pc in project_full.classes] if project_full and project_full.classes else []
        if student.class_id not in valid_class_ids:
            from app.core.exceptions import PermissionDeniedException
            raise PermissionDeniedException("你不在该项目关联的班级中，无法提交作业")

        submission = Submission(
            id=str(uuid.uuid4()),
            task_id=task_id,
            student_id=student.id,
            group_name=group_name,
            content=content,
            attachments=attachments or [],
            status="submitted",
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(submission)
        await db.flush()

        # Reload with relationships for response formatting
        result = await db.execute(
            select(Submission)
            .options(
                selectinload(Submission.student),
                selectinload(Submission.task),
                selectinload(Submission.evaluations),
            )
            .where(Submission.id == submission.id)
        )
        submission = result.unique().scalar_one()
        return submission

    @staticmethod
    async def list_task_submissions(
        db: AsyncSession,
        task_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> dict:
        """List submissions for a task (teacher view)."""
        # Verify task exists
        await TaskService.get_task(db, task_id)

        query = (
            select(Submission)
            .options(
                selectinload(Submission.student),
                selectinload(Submission.task),
                selectinload(Submission.evaluations),
            )
            .where(Submission.task_id == task_id)
        )
        count_base = (
            select(func.count())
            .select_from(Submission)
            .where(Submission.task_id == task_id)
        )

        if status:
            query = query.where(Submission.status == status)
            count_base = count_base.where(Submission.status == status)

        total_result = await db.execute(count_base)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(Submission.submitted_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        submissions = result.unique().scalars().all()

        items = []
        for sub in submissions:
            items.append({
                "id": sub.id,
                "task_id": sub.task_id,
                "student_id": sub.student_id,
                "student_name": sub.student.name if sub.student else None,
                "group_name": sub.group_name,
                "content": sub.content,
                "attachments": sub.attachments,
                "status": sub.status,
                "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }


def _format_task_item(task: Task) -> dict:
    """Format a task model instance into a response dict."""
    return {
        "id": task.id,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "submit_type": task.submit_type,
        "rubric_id": task.rubric_id,
        "rubric_name": task.rubric.name if task.rubric else None,
        "due_at": task.due_at.isoformat() if task.due_at else None,
        "status": task.status,
        "submission_count": len(task.submissions) if task.submissions else 0,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
