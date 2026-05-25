"""Evaluation-related Pydantic schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    """Schema for creating a new evaluation."""

    submission_id: str
    rubric_id: str
    scores: dict[str, int] = {}
    comments: Optional[str] = Field(None, max_length=5000)
    evaluator_type: str = Field(default="teacher", pattern="^(teacher|self|peer|ai)$")


class EvaluationUpdate(BaseModel):
    """Schema for updating an existing evaluation (only when draft)."""

    scores: Optional[dict[str, int]] = None
    comments: Optional[str] = Field(None, max_length=5000)


class EvaluationResponse(BaseModel):
    """Schema for evaluation response data."""

    id: str
    submission_id: str
    evaluator_id: str
    evaluator_name: Optional[str] = None
    evaluator_type: str
    rubric_id: str
    rubric_name: Optional[str] = None
    scores: Optional[dict] = None
    comments: Optional[str] = None
    status: str
    confirmed_by: Optional[str] = None
    confirmer_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
