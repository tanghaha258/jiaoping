"""User management endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_roles
from app.core.response import success_response
from app.models.user import User
from app.schemas.user import (
    ResetPasswordRequest,
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.user_service import UserService

router = APIRouter(prefix="/users")


@router.get("")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    keyword: str = Query(default=None),
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
        keyword=keyword,
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
    return success_response(data=user_response.model_dump(), message="User created")


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
    return success_response(data=user_response.model_dump(), message="User updated")


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
    return success_response(data=user_response.model_dump(), message="User status updated")


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin")),
):
    """Reset a user's password as a system administrator."""
    user = await UserService.reset_password(db=db, user_id=user_id, new_password=data.new_password)
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="user.reset_password",
        target_type="user",
        target_id=user.id,
        detail={"target_username": user.username},
    )
    return success_response(data={"updated": True, "user_id": user.id}, message="Password reset")
