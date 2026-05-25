"""Authentication service: login, token creation, refresh."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import InvalidCredentialsException, InvalidStateTransitionException, TokenExpiredException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserInfo


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> dict:
        """Validate credentials and return tokens with user info."""
        result = await db.execute(
            select(User).options(selectinload(User.school)).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsException("用户名或密码错误")

        if user.status != "active":
            raise InvalidCredentialsException("账户已被禁用，请联系管理员")

        # Update last login time
        user.last_login_at = datetime.now(timezone.utc)
        db.add(user)
        await db.flush()

        return AuthService._build_token_response(user)

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str,
    ) -> dict:
        """Create a new access token from a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise TokenExpiredException("Refresh token is invalid or expired")

        if payload.get("type") != "refresh":
            raise InvalidCredentialsException("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsException("Invalid token payload")

        result = await db.execute(
            select(User).options(selectinload(User.school)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user is None or user.status != "active":
            raise InvalidCredentialsException("User not found or inactive")

        return AuthService._build_token_response(user)

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> User:
        """Change the current user's password after verifying the old password."""
        if not verify_password(current_password, user.password_hash):
            raise InvalidStateTransitionException("Current password is incorrect")

        if verify_password(new_password, user.password_hash):
            raise InvalidStateTransitionException("New password must be different")

        user.password_hash = hash_password(new_password)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    def _build_token_response(user: User) -> dict:
        """Build the token response dict for a given user."""
        token_data = {"sub": user.id, "username": user.username, "role": user.role}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        user_info = UserInfo(
            id=user.id,
            username=user.username,
            name=user.name,
            role=user.role,
            school_id=user.school_id,
            school_name=user.school.name if user.school else None,
            class_id=user.class_id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user_info.model_dump(),
        }
