"""AIAgent model."""

from sqlalchemy import Column, String, JSON, Boolean

from app.db.base import Base, CommonMixin


class AIAgent(Base, CommonMixin):
    __tablename__ = "ai_agents"

    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False, default="mock")
    scenario = Column(String(50), nullable=False)
    config = Column(JSON, nullable=True, default=dict)
    input_schema = Column(JSON, nullable=True, default=dict)
    output_schema = Column(JSON, nullable=True, default=dict)
    enabled = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<AIAgent(name={self.name}, scenario={self.scenario})>"
