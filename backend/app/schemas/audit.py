"""Audit log Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AuditLogFilter(BaseModel):
    """Query parameters for filtering audit logs."""

    action: Optional[str] = Field(default=None, description="Filter by action (e.g. 'project.create')")
    target_type: Optional[str] = Field(default=None, description="Filter by target type (e.g. 'project')")
    user_id: Optional[str] = Field(default=None, description="Filter by user ID")
    start_date: Optional[datetime] = Field(default=None, description="Filter logs created after this date")
    end_date: Optional[datetime] = Field(default=None, description="Filter logs created before this date")


class AuditLogResponse(BaseModel):
    """Audit log entry in API responses."""

    id: str
    user_id: str
    user_name: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    detail: Optional[dict] = None
    created_at: str

    class Config:
        from_attributes = True
