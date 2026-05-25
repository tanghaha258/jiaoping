"""FastAPI dependency injection helpers."""

import uuid
from typing import AsyncGenerator, List

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import InvalidCredentialsException, PermissionDeniedException, ResourceNotFoundException
from app.core.security import decode_token
from app.db.session import AsyncSessionFactory
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that extracts and validates the current user from JWT."""
    if credentials is None:
        raise InvalidCredentialsException("Missing authentication token")

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise InvalidCredentialsException("Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidCredentialsException("Invalid token payload")

    result = await db.execute(
        select(User).options(selectinload(User.school)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ResourceNotFoundException("User not found")

    if user.status != "active":
        raise PermissionDeniedException("User account is not active")

    return user


def require_roles(*roles: str):
    """Dependency factory: requires the current user to have at least one of the specified roles."""

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise PermissionDeniedException(
                f"Required role(s): {', '.join(roles)}. Your role: {current_user.role}"
            )
        return current_user

    return role_checker


async def get_trace_id(request: Request) -> str:
    """Dependency that extracts or generates a trace ID for the request."""
    trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        trace_id = f"req_{uuid.uuid4().hex[:12]}"
    return trace_id
