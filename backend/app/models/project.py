"""Project model."""

from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Project(Base, CommonMixin):
    __tablename__ = "projects"

    school_id = Column(CHAR(36), ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    grade = Column(String(50), nullable=False)
    driving_question = Column(String(500), nullable=True)
    objectives = Column(JSON, nullable=True, default=list)
    lesson_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft")
    owner_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    school = relationship("School", backref="projects")
    owner = relationship("User", backref="owned_projects", foreign_keys=[owner_id])
    lessons = relationship("ProjectLesson", back_populates="project", order_by="ProjectLesson.lesson_order")
    subjects = relationship("ProjectSubject", back_populates="project", cascade="all, delete-orphan")
    classes = relationship("ProjectClass", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project")

    def __repr__(self):
        return f"<Project(name={self.name}, status={self.status})>"
