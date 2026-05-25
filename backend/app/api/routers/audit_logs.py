"""Audit log API endpoints — admin-only access."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.deps import get_current_user, get_db, require_roles
from app.core.response import success_response, paginated_response
from app.core.exceptions import ResourceNotFoundException
from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs")


@router.get("")
async def list_audit_logs(
    action: Optional[str] = Query(default=None, description="Filter by action"),
    target_type: Optional[str] = Query(default=None, description="Filter by target type"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(default=None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(default=None, description="End date (ISO format)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    """List audit logs with pagination and filters. Admin-only: system_admin or school_admin."""
    query = select(AuditLog).options(joinedload(AuditLog.user))
    count_base = select(func.count()).select_from(AuditLog)

    # Apply filters
    if action:
        query = query.where(AuditLog.action == action)
        count_base = count_base.where(AuditLog.action == action)
    if target_type:
        query = query.where(AuditLog.target_type == target_type)
        count_base = count_base.where(AuditLog.target_type == target_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_base = count_base.where(AuditLog.user_id == user_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
        count_base = count_base.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
        count_base = count_base.where(AuditLog.created_at <= end_date)

    # For school_admin, restrict to users in the same school
    if current_user.role == "school_admin" and current_user.school_id:
        # Join with users to filter by school_id
        query = query.join(User, AuditLog.user_id == User.id).where(
            User.school_id == current_user.school_id
        )
        count_base = (
            count_base.join(User, AuditLog.user_id == User.id)
            .where(User.school_id == current_user.school_id)
        )

    # Count total
    total_result = await db.execute(count_base)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.unique().scalars().all()

    # Build response items
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "ip": log.ip,
            "user_agent": log.user_agent,
            "detail": log.detail,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}")
async def get_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("system_admin", "school_admin")),
):
    """Get a single audit log entry by ID. Admin-only."""
    result = await db.execute(
        select(AuditLog)
        .options(joinedload(AuditLog.user))
        .where(AuditLog.id == log_id)
    )
    log = result.unique().scalar_one_or_none()

    if log is None:
        raise ResourceNotFoundException("审计日志不存在")

    # For school_admin, ensure the log's user belongs to the admin's school
    if current_user.role == "school_admin" and current_user.school_id:
        if log.user is None or log.user.school_id != current_user.school_id:
            raise ResourceNotFoundException("审计日志不存在")

    return success_response(data={
        "id": log.id,
        "user_id": log.user_id,
        "user_name": log.user.name if log.user else None,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "ip": log.ip,
        "user_agent": log.user_agent,
        "detail": log.detail,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    })
