"""Rubric management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.rubric import RubricCreate, RubricUpdate
from app.services.rubric_service import RubricService, _format_rubric_item

router = APIRouter(prefix="/rubrics")


@router.get("")
async def list_rubrics(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    scope: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List rubrics with pagination.

    Teachers see their own rubrics plus school-scoped ones.
    Admins see all rubrics.
    """
    result = await RubricService.list_rubrics(
        db=db,
        page=page,
        page_size=page_size,
        scope=scope,
        current_user=current_user,
    )
    return success_response(data=result)


@router.post("")
async def create_rubric(
    data: RubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Create a new rubric with its criterion items. Teacher only."""
    rubric = await RubricService.create_rubric(db=db, data=data, user=current_user)
    rubric_full = await RubricService.get_rubric(db=db, rubric_id=rubric.id)
    return success_response(data=_format_rubric_item(rubric_full), message="量规创建成功")


@router.get("/{rubric_id}")
async def get_rubric(
    rubric_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get rubric details by ID."""
    rubric = await RubricService.get_rubric(db=db, rubric_id=rubric_id)
    return success_response(data=_format_rubric_item(rubric))


@router.patch("/{rubric_id}")
async def update_rubric(
    rubric_id: str,
    data: RubricUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("teacher")),
):
    """Update a rubric and optionally replace its items. Teacher only."""
    rubric = await RubricService.update_rubric(db=db, rubric_id=rubric_id, data=data)
    rubric_full = await RubricService.get_rubric(db=db, rubric_id=rubric.id)
    return success_response(data=_format_rubric_item(rubric_full), message="量规更新成功")
