"""User-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=50)
    school_id: Optional[str] = None
    class_id: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None
    role: Optional[str] = Field(None, max_length=50)
    school_id: Optional[str] = None
    class_id: Optional[str] = None


class UserStatusUpdate(BaseModel):
    """Schema for updating user status."""

    status: str = Field(..., pattern="^(active|disabled|locked)$")


class UserResponse(BaseModel):
    """Schema for user response data."""

    id: str
    username: str
    name: str
    role: str
    school_id: Optional[str] = None
    school_name: Optional[str] = None
    class_id: Optional[str] = None
    status: str
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
