"""Submission-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    """Schema for a student submitting work to a task."""

    content: Optional[str] = Field(None, max_length=10000)
    group_name: Optional[str] = Field(None, max_length=100)
    attachments: Optional[list[dict]] = []


class SubmissionUpdate(BaseModel):
    """Schema for updating an existing submission (resubmit)."""

    content: Optional[str] = Field(None, max_length=10000)
    group_name: Optional[str] = Field(None, max_length=100)
    attachments: Optional[list[dict]] = None


class SubmissionResponse(BaseModel):
    """Schema for submission response data."""

    id: str
    task_id: str
    task_title: Optional[str] = None
    student_id: str
    student_name: Optional[str] = None
    group_name: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[list] = None
    status: str
    submitted_at: Optional[datetime] = None
    evaluation_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
