"""Project-Class junction table model."""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProjectClass(Base):
    __tablename__ = "project_classes"

    project_id = Column(CHAR(36), ForeignKey("projects.id"), primary_key=True)
    class_id = Column(CHAR(36), ForeignKey("classes.id"), primary_key=True)

    # Relationships
    project = relationship("Project", back_populates="classes")
    target_class = relationship("Class")

    def __repr__(self):
        return f"<ProjectClass(project_id={self.project_id}, class_id={self.class_id})>"
