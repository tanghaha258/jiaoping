"""Rubric service: CRUD operations with nested rubric_items management."""

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundException
from app.models.rubric import Rubric
from app.models.rubric_item import RubricItem
from app.models.user import User
from app.schemas.rubric import RubricCreate, RubricUpdate


class RubricService:
    """Service for rubric management operations."""

    @staticmethod
    async def list_rubrics(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        scope: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> dict:
        """List rubrics with pagination and optional filters.

        Teachers see their own rubrics plus school-scoped ones.
        Admins see all rubrics.
        """
        query = (
            select(Rubric)
            .options(
                selectinload(Rubric.items),
                selectinload(Rubric.creator),
            )
        )
        count_base = select(func.count()).select_from(Rubric)

        if scope:
            query = query.where(Rubric.scope == scope)
            count_base = count_base.where(Rubric.scope == scope)

        # RBAC filtering
        if current_user is not None:
            if current_user.role == "teacher":
                query = query.where(
                    (Rubric.created_by == current_user.id)
                    | (Rubric.scope.in_(["school", "region", "system"]))
                    | ((Rubric.school_id == current_user.school_id) & (Rubric.scope == "school"))
                )
                count_base = count_base.where(
                    (Rubric.created_by == current_user.id)
                    | (Rubric.scope.in_(["school", "region", "system"]))
                    | ((Rubric.school_id == current_user.school_id) & (Rubric.scope == "school"))
                )
            elif current_user.role == "system_admin":
                pass  # Admins see all
            else:
                # Students see school/system rubrics
                query = query.where(
                    Rubric.scope.in_(["school", "region", "system"])
                )
                count_base = count_base.where(
                    Rubric.scope.in_(["school", "region", "system"])
                )

        total_result = await db.execute(count_base)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(Rubric.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        rubrics = result.unique().scalars().all()

        items = [_format_rubric_item(rubric) for rubric in rubrics]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }

    @staticmethod
    async def create_rubric(
        db: AsyncSession, data: RubricCreate, user: User
    ) -> Rubric:
        """Create a new rubric with its nested rubric items."""
        rubric = Rubric(
            id=str(uuid.uuid4()),
            school_id=user.school_id,
            name=data.name,
            description=data.description,
            scope=data.scope,
            created_by=user.id,
        )
        db.add(rubric)

        # Create rubric items
        for idx, item_data in enumerate(data.items):
            levels = _build_levels(item_data)
            rubric_item = RubricItem(
                id=str(uuid.uuid4()),
                rubric_id=rubric.id,
                dimension=item_data.dimension,
                weight=Decimal(str(item_data.weight)),
                levels=levels,
                sort_order=idx,
            )
            db.add(rubric_item)

        await db.flush()
        await db.refresh(rubric)
        return rubric

    @staticmethod
    async def get_rubric(db: AsyncSession, rubric_id: str) -> Rubric:
        """Get a rubric by ID with its items loaded."""
        result = await db.execute(
            select(Rubric)
            .options(
                selectinload(Rubric.items),
                selectinload(Rubric.creator),
            )
            .where(Rubric.id == rubric_id)
        )
        rubric = result.unique().scalar_one_or_none()
        if rubric is None:
            raise ResourceNotFoundException("量规不存在")
        return rubric

    @staticmethod
    async def update_rubric(
        db: AsyncSession, rubric_id: str, data: RubricUpdate
    ) -> Rubric:
        """Update a rubric's fields and optionally its items."""
        rubric = await RubricService.get_rubric(db, rubric_id)

        update_data = data.model_dump(exclude_unset=True)
        items_data = update_data.pop("items", None)

        # Update scalar fields
        for key, value in update_data.items():
            if value is not None:
                setattr(rubric, key, value)

        # Replace items if provided
        if items_data is not None:
            # Delete existing items
            existing_items = (
                await db.execute(
                    select(RubricItem).where(RubricItem.rubric_id == rubric_id)
                )
            ).scalars().all()
            for ri in existing_items:
                await db.delete(ri)

            # Create new items
            for idx, item_data in enumerate(items_data):
                levels = _build_levels(item_data)
                rubric_item = RubricItem(
                    id=str(uuid.uuid4()),
                    rubric_id=rubric_id,
                    dimension=item_data.dimension,
                    weight=Decimal(str(item_data.weight)),
                    levels=levels,
                    sort_order=idx,
                )
                db.add(rubric_item)

        db.add(rubric)
        await db.flush()
        await db.refresh(rubric)
        return rubric


def _build_levels(item_data) -> list:
    """Convert flat level_a/b/c/d fields into a levels JSON list."""
    levels = []
    for grade_label in ("A", "B", "C", "D"):
        field_name = f"level_{grade_label.lower()}"
        desc = getattr(item_data, field_name, "") or ""
        if desc:
            levels.append({"grade": grade_label, "description": desc})
    return levels


def _format_rubric_item(rubric: Rubric) -> dict:
    """Format a rubric model instance into a response dict."""
    items = []
    if rubric.items:
        for ri in sorted(rubric.items, key=lambda x: x.sort_order):
            items.append({
                "id": ri.id,
                "dimension": ri.dimension,
                "weight": float(ri.weight) if ri.weight else 0.0,
                "levels": ri.levels or [],
                "sort_order": ri.sort_order,
            })

    return {
        "id": rubric.id,
        "school_id": rubric.school_id,
        "name": rubric.name,
        "description": rubric.description,
        "scope": rubric.scope,
        "created_by": rubric.created_by,
        "creator_name": rubric.creator.name if rubric.creator else None,
        "items": items,
        "created_at": rubric.created_at.isoformat() if rubric.created_at else None,
        "updated_at": rubric.updated_at.isoformat() if rubric.updated_at else None,
    }
