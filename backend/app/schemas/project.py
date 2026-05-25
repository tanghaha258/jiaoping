"""Project-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=200)
    grade: str = Field(..., min_length=1, max_length=50)
    subject_ids: list[str] = Field(..., min_length=1)
    class_ids: list[str] = Field(..., min_length=1)
    driving_question: str = Field(..., max_length=500)
    lesson_count: int = Field(ge=1, le=20)
    objectives: list[str] = []


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    grade: Optional[str] = Field(None, min_length=1, max_length=50)
    subject_ids: Optional[list[str]] = None
    class_ids: Optional[list[str]] = None
    driving_question: Optional[str] = Field(None, max_length=500)
    lesson_count: Optional[int] = Field(None, ge=1, le=20)
    objectives: Optional[list[str]] = None


class ProjectResponse(BaseModel):
    """Schema for project response data."""

    id: str
    school_id: str
    name: str
    grade: str
    driving_question: Optional[str] = None
    objectives: list = []
    lesson_count: int
    status: str
    owner_id: str
    owner_name: Optional[str] = None
    subjects: list[dict] = []
    classes: list[dict] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
