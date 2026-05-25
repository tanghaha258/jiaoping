"""Evaluation management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate
from app.services.evaluation_service import EvaluationService, _format_evaluation_item

router = APIRouter(prefix="/evaluations")


@router.get("")
async def list_evaluations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    submission_id: str = Query(default=None),
    evaluator_id: str = Query(default=None),
    evaluator_type: str = Query(default=None),
    status: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List evaluations with filters.

    Users can filter by submission, evaluator, or status.
    """
    result = await EvaluationService.list_evaluations(
        db=db,
        page=page,
        page_size=page_size,
        submission_id=submission_id,
        evaluator_id=evaluator_id,
        evaluator_type=evaluator_type,
        status=status,
        current_user=current_user,
    )
    return success_response(data=result)


@router.post("")
async def create_evaluation(
    data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new evaluation for a submission.

    Teachers, students (self/peer), and AI agents can create evaluations.
    """
    eval_obj = await EvaluationService.create_evaluation(db=db, data=data, user=current_user)
    eval_full = await EvaluationService.get_evaluation(db=db, evaluation_id=eval_obj.id)
    return success_response(data=_format_evaluation_item(eval_full), message="评价创建成功")


@router.get("/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get evaluation details by ID."""
    evaluation = await EvaluationService.get_evaluation(
        db=db,
        evaluation_id=evaluation_id,
        current_user=current_user,
    )
    return success_response(data=_format_evaluation_item(evaluation))


@router.patch("/{evaluation_id}")
async def update_evaluation(
    evaluation_id: str,
    data: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an evaluation. Only draft evaluations can be updated."""
    evaluation = await EvaluationService.update_evaluation(
        db=db, evaluation_id=evaluation_id, data=data, user=current_user
    )
    eval_full = await EvaluationService.get_evaluation(db=db, evaluation_id=evaluation.id)
    return success_response(data=_format_evaluation_item(eval_full), message="评价更新成功")


@router.post("/{evaluation_id}/confirm")
async def confirm_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Teacher confirms an evaluation (draft -> confirmed). Teacher only."""
    evaluation = await EvaluationService.confirm_evaluation(
        db=db, evaluation_id=evaluation_id, user=current_user
    )
    eval_full = await EvaluationService.get_evaluation(db=db, evaluation_id=evaluation.id)
    return success_response(data=_format_evaluation_item(eval_full), message="评价已确认")
