"""Authentication-related Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""

    username: str = Field(..., min_length=2, max_length=100, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class UserInfo(BaseModel):
    """User information embedded in token responses."""

    id: str
    username: str
    name: str
    role: str
    school_id: Optional[str] = None
    school_name: Optional[str] = None
    class_id: Optional[str] = None


class TokenResponse(BaseModel):
    """Response returned after successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class RefreshRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str = Field(..., description="Refresh token")
