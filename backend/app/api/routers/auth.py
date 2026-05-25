"""Authentication endpoints: login, refresh, logout, current user."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.response import success_response
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserInfo
from app.services.auth_service import AuthService
from app.services.audit_service import create_audit_log

router = APIRouter(prefix="/auth")


@router.post("/login")
async def login(request: LoginRequest, fastapi_request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    result = await AuthService.authenticate(
        db=db,
        username=request.username,
        password=request.password,
    )

    # Audit log: record successful login
    user_id = result.get("user", {}).get("id")
    if user_id:
        await create_audit_log(
            db=db,
            user_id=user_id,
            action="user.login",
            target_type="user",
            target_id=user_id,
            ip=fastapi_request.client.host if fastapi_request.client else None,
            user_agent=fastapi_request.headers.get("user-agent"),
        )

    return success_response(data=result, message="登录成功")


@router.post("/refresh")
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    result = await AuthService.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
    )
    return success_response(data=result, message="Token refreshed")


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """Logout current user. (Token invalidation is handled client-side for JWT.)"""
    return success_response(data=None, message="已退出登录")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user info."""
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        role=current_user.role,
        school_id=current_user.school_id,
        school_name=current_user.school.name if current_user.school else None,
        class_id=current_user.class_id,
    )
    return success_response(data=user_info.model_dump())
