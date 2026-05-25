"""School model."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class School(Base, CommonMixin):
    __tablename__ = "schools"

    region_id = Column(CHAR(36), ForeignKey("regions.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")

    # Relationships
    region = relationship("Region", backref="schools")
    classes = relationship("Class", back_populates="school", foreign_keys="Class.school_id")

    def __repr__(self):
        return f"<School(name={self.name}, code={self.code})>"
