"""User management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.common import PaginationParams
from app.schemas.user import UserCreate, UserUpdate, UserStatusUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users")


@router.get("")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str = Query(default=None),
    status: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "teacher")),
):
    """List users with pagination and filters."""
    result = await UserService.list_users(
        db=db,
        page=page,
        page_size=page_size,
        role=role,
        status=status,
    )
    return success_response(data=result)


@router.post("")
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    """Create a new user."""
    user = await UserService.create_user(db=db, data=data)
    user_response = UserResponse.model_validate(user)
    return success_response(data=user_response.model_dump(), message="用户创建成功")


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "teacher")),
):
    """Get user details by ID."""
    user = await UserService.get_user(db=db, user_id=user_id)
    user_response = UserResponse.model_validate(user)
    return success_response(data=user_response.model_dump())


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    """Update user information."""
    user = await UserService.update_user(db=db, user_id=user_id, data=data)
    user_response = UserResponse.model_validate(user)
    return success_response(data=user_response.model_dump(), message="用户更新成功")


@router.patch("/{user_id}/status")
async def change_user_status(
    user_id: str,
    data: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    """Enable or disable a user account."""
    user = await UserService.change_user_status(db=db, user_id=user_id, status=data.status)
    user_response = UserResponse.model_validate(user)
    return success_response(data=user_response.model_dump(), message="用户状态更新成功")
