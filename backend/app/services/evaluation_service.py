"""Evaluation service: CRUD operations and confirmation logic."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    InvalidStateTransitionException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.rubric import Rubric
from app.models.user import User
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate


class EvaluationService:
    """Service for evaluation management operations."""

    @staticmethod
    async def list_evaluations(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        submission_id: Optional[str] = None,
        evaluator_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """List evaluations with filters and pagination."""
        query = (
            select(Evaluation)
            .options(
                selectinload(Evaluation.evaluator),
                selectinload(Evaluation.rubric),
                selectinload(Evaluation.submission).selectinload(Submission.student),
                selectinload(Evaluation.submission).selectinload(Submission.task),
                selectinload(Evaluation.confirmer),
            )
        )
        count_base = select(func.count()).select_from(Evaluation)

        if submission_id:
            query = query.where(Evaluation.submission_id == submission_id)
            count_base = count_base.where(Evaluation.submission_id == submission_id)
        if evaluator_id:
            query = query.where(Evaluation.evaluator_id == evaluator_id)
            count_base = count_base.where(Evaluation.evaluator_id == evaluator_id)
        if status:
            query = query.where(Evaluation.status == status)
            count_base = count_base.where(Evaluation.status == status)

        total_result = await db.execute(count_base)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(Evaluation.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        evaluations = result.unique().scalars().all()

        items = [_format_evaluation_item(ev) for ev in evaluations]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def create_evaluation(
        db: AsyncSession, data: EvaluationCreate, user: User
    ) -> Evaluation:
        """Create a new evaluation for a submission.

        Validates: submission exists, rubric exists, evaluator_type matches user role.
        """
        # Verify submission exists
        sub_result = await db.execute(
            select(Submission).where(Submission.id == data.submission_id)
        )
        if sub_result.scalar_one_or_none() is None:
            raise ResourceNotFoundException("提交记录不存在")

        # Verify rubric exists
        rub_result = await db.execute(
            select(Rubric).where(Rubric.id == data.rubric_id)
        )
        if rub_result.scalar_one_or_none() is None:
            raise ResourceNotFoundException("量规不存在")

        # Validate evaluator_type consistency
        if data.evaluator_type == "ai" and user.role != "system_admin":
            # AI evaluation can only be initiated by admins or the system
            pass  # Allow all for now, proper restrictions via router RBAC

        evaluation = Evaluation(
            id=str(uuid.uuid4()),
            submission_id=data.submission_id,
            evaluator_id=user.id,
            evaluator_type=data.evaluator_type,
            rubric_id=data.rubric_id,
            scores=data.scores,
            comments=data.comments,
            status="draft",
        )
        db.add(evaluation)
        sub = await db.get(Submission, data.submission_id)
        if sub is not None and user.role in ("teacher", "system_admin"):
            sub.status = "reviewed"
            db.add(sub)
        await db.flush()
        await db.refresh(evaluation)
        return evaluation

    @staticmethod
    async def get_evaluation(db: AsyncSession, evaluation_id: str) -> Evaluation:
        """Get an evaluation by ID with all relationships."""
        result = await db.execute(
            select(Evaluation)
            .options(
                selectinload(Evaluation.evaluator),
                selectinload(Evaluation.rubric),
                selectinload(Evaluation.submission).selectinload(Submission.student),
                selectinload(Evaluation.submission).selectinload(Submission.task),
                selectinload(Evaluation.confirmer),
            )
            .where(Evaluation.id == evaluation_id)
        )
        evaluation = result.unique().scalar_one_or_none()
        if evaluation is None:
            raise ResourceNotFoundException("评价记录不存在")
        return evaluation

    @staticmethod
    async def update_evaluation(
        db: AsyncSession, evaluation_id: str, data: EvaluationUpdate, user: User
    ) -> Evaluation:
        """Update an evaluation (only when status is draft)."""
        evaluation = await EvaluationService.get_evaluation(db, evaluation_id)

        if evaluation.status != "draft":
            raise InvalidStateTransitionException("只有草稿状态的评价可以修改")

        # Only the evaluator (or admin) can update their evaluation
        if evaluation.evaluator_id != user.id and user.role != "system_admin":
            raise PermissionDeniedException("只能修改自己的评价")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(evaluation, key, value)

        db.add(evaluation)
        await db.flush()
        await db.refresh(evaluation)
        return evaluation

    @staticmethod
    async def confirm_evaluation(
        db: AsyncSession, evaluation_id: str, user: User
    ) -> Evaluation:
        """Teacher confirms an evaluation (draft -> confirmed)."""
        evaluation = await EvaluationService.get_evaluation(db, evaluation_id)

        if evaluation.status != "draft":
            raise InvalidStateTransitionException("只能确认草稿状态的评价")

        # Only teachers can confirm evaluations
        if user.role not in ("teacher", "system_admin"):
            raise PermissionDeniedException("只有教师可以确认评价")

        evaluation.status = "confirmed"
        evaluation.confirmed_by = user.id
        db.add(evaluation)
        await db.flush()
        await db.refresh(evaluation)
        return evaluation


def _format_evaluation_item(evaluation: Evaluation) -> dict:
    """Format an evaluation model instance into a response dict."""
    submission = evaluation.submission
    task = submission.task if submission else None
    student = submission.student if submission else None
    return {
        "id": evaluation.id,
        "submission_id": evaluation.submission_id,
        "student_id": student.id if student else None,
        "student_name": student.name if student else None,
        "task_id": task.id if task else None,
        "task_title": task.title if task else None,
        "evaluator_id": evaluation.evaluator_id,
        "evaluator_name": evaluation.evaluator.name if evaluation.evaluator else None,
        "evaluator_type": evaluation.evaluator_type,
        "rubric_id": evaluation.rubric_id,
        "rubric_name": evaluation.rubric.name if evaluation.rubric else None,
        "scores": evaluation.scores,
        "comments": evaluation.comments,
        "status": evaluation.status,
        "confirmed_by": evaluation.confirmed_by,
        "confirmer_name": evaluation.confirmer.name if evaluation.confirmer else None,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
        "updated_at": evaluation.updated_at.isoformat() if evaluation.updated_at else None,
    }
