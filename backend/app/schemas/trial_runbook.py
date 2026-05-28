"""Schemas for trial operations runbook evidence records."""

from typing import Literal

from pydantic import BaseModel, Field


class TrialRunbookRecordCreate(BaseModel):
    """Payload for appending one runbook rehearsal record."""

    status: Literal["checked", "blocked", "skipped"]
    note: str = Field(default="", max_length=500)
    evidence: list[str] = Field(default_factory=list, max_length=8)
