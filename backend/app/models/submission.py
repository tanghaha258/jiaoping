"""Submission model."""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Submission(Base, CommonMixin):
    __tablename__ = "submissions"

    task_id = Column(CHAR(36), ForeignKey("tasks.id"), nullable=False, index=True)
    student_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    group_name = Column(String(100), nullable=True)
    content = Column(String(10000), nullable=True)
    attachments = Column(JSON, nullable=True, default=list)
    status = Column(String(20), nullable=False, default="draft")
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("Task", back_populates="submissions")
    student = relationship("User", backref="submissions", foreign_keys=[student_id])
    evaluations = relationship("Evaluation", back_populates="submission")

    def __repr__(self):
        return f"<Submission(task_id={self.task_id}, status={self.status})>"
