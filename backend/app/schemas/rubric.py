"""Rubric-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RubricItemCreate(BaseModel):
    """Schema for creating a rubric criterion item."""

    dimension: str = Field(..., min_length=1, max_length=200)
    weight: float = Field(..., ge=0.0, le=100.0)
    level_a: str = ""
    level_b: str = ""
    level_c: str = ""
    level_d: str = ""


class RubricItemUpdate(BaseModel):
    """Schema for updating a rubric criterion item."""

    dimension: Optional[str] = Field(None, min_length=1, max_length=200)
    weight: Optional[float] = Field(None, ge=0.0, le=100.0)
    level_a: Optional[str] = None
    level_b: Optional[str] = None
    level_c: Optional[str] = None
    level_d: Optional[str] = None


class RubricItemResponse(BaseModel):
    """Schema for rubric item response data."""

    id: str
    dimension: str
    weight: float
    levels: list[dict] = []
    sort_order: int = 0

    model_config = {"from_attributes": True}


class RubricCreate(BaseModel):
    """Schema for creating a new rubric."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    scope: str = Field(default="personal", pattern="^(personal|school|region|system)$")
    items: list[RubricItemCreate] = []


class RubricUpdate(BaseModel):
    """Schema for updating an existing rubric."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    scope: Optional[str] = Field(None, pattern="^(personal|school|region|system)$")
    items: Optional[list[RubricItemCreate]] = None


class RubricResponse(BaseModel):
    """Schema for rubric response data."""

    id: str
    school_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    scope: str
    created_by: str
    creator_name: Optional[str] = None
    items: list[RubricItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
