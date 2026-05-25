"""Task model."""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Task(Base, CommonMixin):
    __tablename__ = "tasks"

    project_id = Column(CHAR(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    task_type = Column(String(20), nullable=False, default="individual")
    submit_type = Column(String(20), nullable=False, default="text")
    rubric_id = Column(CHAR(36), ForeignKey("rubrics.id"), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="draft")

    # Relationships
    project = relationship("Project", back_populates="tasks")
    rubric = relationship("Rubric", backref="tasks")
    submissions = relationship("Submission", back_populates="task")

    def __repr__(self):
        return f"<Task(title={self.title}, status={self.status})>"
