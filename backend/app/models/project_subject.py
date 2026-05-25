"""Project-Subject junction table model."""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProjectSubject(Base):
    __tablename__ = "project_subjects"

    project_id = Column(CHAR(36), ForeignKey("projects.id"), primary_key=True)
    subject_id = Column(CHAR(36), ForeignKey("subjects.id"), primary_key=True)

    # Relationships
    project = relationship("Project", back_populates="subjects")
    subject = relationship("Subject")

    def __repr__(self):
        return f"<ProjectSubject(project_id={self.project_id}, subject_id={self.subject_id})>"
