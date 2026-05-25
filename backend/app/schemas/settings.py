"""Schemas for system settings management."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class SettingUpsert(BaseModel):
    value: Any = Field(...)
    description: Optional[str] = Field(None, max_length=500)
