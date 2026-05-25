"""Class (班级) model."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Class(Base, CommonMixin):
    __tablename__ = "classes"

    school_id = Column(CHAR(36), ForeignKey("schools.id"), nullable=False, index=True)
    grade = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False)

    # Relationships
    school = relationship("School", back_populates="classes", foreign_keys=[school_id])

    def __repr__(self):
        return f"<Class(name={self.name}, grade={self.grade})>"
