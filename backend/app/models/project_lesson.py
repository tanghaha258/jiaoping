"""ProjectLesson model."""

from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class ProjectLesson(Base, CommonMixin):
    __tablename__ = "project_lessons"

    project_id = Column(CHAR(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    lesson_order = Column(Integer, nullable=False)
    content = Column(JSON, nullable=True, default=dict)

    # Relationships
    project = relationship("Project", back_populates="lessons")

    def __repr__(self):
        return f"<ProjectLesson(title={self.title}, order={self.lesson_order})>"
