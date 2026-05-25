"""AI call thinking/progress step model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class AICallStep(Base, CommonMixin):
    """Observable progress step for one AI call."""

    __tablename__ = "ai_call_steps"

    call_id = Column(CHAR(36), ForeignKey("ai_agent_calls.id"), nullable=False, index=True)
    code = Column(String(80), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    percent = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)

    call = relationship("AIAgentCall", back_populates="steps")

    def __repr__(self):
        return f"<AICallStep(call_id={self.call_id}, code={self.code}, status={self.status})>"
