"""AuditLog model."""

from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, UUIDPrimaryKeyMixin, utcnow


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Audit log entries - append only, no updates or soft-deletes."""

    __tablename__ = "audit_logs"

    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(36), nullable=False)
    ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    detail = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="audit_logs", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AuditLog(action={self.action}, target_type={self.target_type})>"
