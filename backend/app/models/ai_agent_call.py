"""AIAgentCall model."""

from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class AIAgentCall(Base, CommonMixin):
    __tablename__ = "ai_agent_calls"

    agent_id = Column(CHAR(36), ForeignKey("ai_agents.id"), nullable=False, index=True)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    school_id = Column(CHAR(36), ForeignKey("schools.id"), nullable=False)
    project_id = Column(CHAR(36), ForeignKey("projects.id"), nullable=True)
    scenario = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    input_summary = Column(String(500), nullable=True)
    output_summary = Column(String(500), nullable=True)
    request_payload = Column(JSON, nullable=True, default=dict)
    response_payload = Column(JSON, nullable=True, default=dict)
    status = Column(String(20), nullable=False, default="created")
    review_status = Column(String(20), nullable=False, default="pending")
    error_message = Column(String(1000), nullable=True)
    diagnostic_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    agent = relationship("AIAgent", backref="calls")
    user = relationship("User", backref="ai_agent_calls", foreign_keys=[user_id])
    school = relationship("School", backref="ai_agent_calls")
    project = relationship("Project", backref="ai_agent_calls")
    steps = relationship(
        "AICallStep",
        back_populates="call",
        cascade="all, delete-orphan",
        order_by="AICallStep.sort_order",
    )

    def __repr__(self):
        return f"<AIAgentCall(agent_id={self.agent_id}, status={self.status})>"
