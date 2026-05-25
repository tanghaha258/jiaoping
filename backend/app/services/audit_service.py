"""Audit service: best-effort audit log creation that never blocks business operations."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def create_audit_log(
    db: AsyncSession,
    user_id: str,
    action: str,
    target_type: str,
    target_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    detail: dict | None = None,
) -> AuditLog | None:
    """Create an audit log entry. Best-effort -- failures should not block the main operation.

    Action naming convention: {target_type}.{operation}
    Examples: project.create, task.publish, submission.create, evaluation.confirm, user.login, ai.call, ai.adopt
    """
    try:
        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip=ip,
            user_agent=user_agent,
            detail=detail or {},
        )
        db.add(log)
        await db.flush()
        return log
    except Exception:
        # Audit failure should never block business operations
        logger.warning(
            "Failed to create audit log: action=%s target_type=%s user_id=%s",
            action,
            target_type,
            user_id,
            exc_info=True,
        )
        return None
