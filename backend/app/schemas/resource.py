"""Resource-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    """Schema for creating a new resource metadata record."""

    title: str = Field(..., min_length=1, max_length=200)
    resource_type: str = Field(..., min_length=1, max_length=50)
    file_path: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = None
    visibility: str = Field(default="school", pattern="^(personal|school|region|system)$")


class ResourceUpdate(BaseModel):
    """Schema for updating an existing resource."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    resource_type: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = None
    visibility: Optional[str] = Field(None, pattern="^(personal|school|region|system)$")


class ResourceResponse(BaseModel):
    """Schema for resource response data."""

    id: str
    school_id: Optional[str] = None
    title: str
    resource_type: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[dict] = None
    visibility: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
