"""User-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


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


class ResetPasswordRequest(BaseModel):
    """Schema for system-admin password reset."""

    new_password: str = Field(..., min_length=6, max_length=100)


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


class UserClassPackageRef(BaseModel):
    """Portable class reference used by user account packages."""

    grade: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    academic_year: str = Field(..., min_length=1, max_length=20)


class UserPackageItem(BaseModel):
    """One account row in the import/export package."""

    model_config = ConfigDict(populate_by_name=True)

    username: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=50)
    school_code: str = Field(..., min_length=1, max_length=50)
    class_ref: Optional[UserClassPackageRef] = Field(default=None, alias="class")
    initial_password: Optional[str] = Field(default=None, min_length=6, max_length=100)


class UserDataPackage(BaseModel):
    """Portable account package."""

    users: list[UserPackageItem] = Field(default_factory=list)


class UserDataImportRequest(BaseModel):
    """Request for validating or importing a user account package."""

    dry_run: bool = True
    package: UserDataPackage
