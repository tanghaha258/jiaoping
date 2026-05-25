"""Rubric model."""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Rubric(Base, CommonMixin):
    __tablename__ = "rubrics"

    school_id = Column(CHAR(36), ForeignKey("schools.id"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    scope = Column(String(20), nullable=False, default="personal")
    created_by = Column(CHAR(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    school = relationship("School", backref="rubrics")
    creator = relationship("User", backref="rubrics", foreign_keys=[created_by])
    items = relationship("RubricItem", back_populates="rubric", order_by="RubricItem.sort_order")

    def __repr__(self):
        return f"<Rubric(name={self.name}, scope={self.scope})>"
