"""Task-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: str = Field(default="individual", pattern="^(individual|group|classroom|homework)$")
    submit_type: str = Field(default="text", pattern="^(text|file|link|mixed)$")
    rubric_id: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: Optional[str] = Field(None, pattern="^(individual|group|classroom|homework)$")
    submit_type: Optional[str] = Field(None, pattern="^(text|file|link|mixed)$")
    rubric_id: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Schema for task response data."""

    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    task_type: str
    submit_type: str
    rubric_id: Optional[str] = None
    rubric_name: Optional[str] = None
    due_at: Optional[datetime] = None
    status: str
    submission_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
