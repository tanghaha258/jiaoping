"""RubricItem model."""

from decimal import Decimal

from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Numeric
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class RubricItem(Base, CommonMixin):
    __tablename__ = "rubric_items"

    rubric_id = Column(CHAR(36), ForeignKey("rubrics.id"), nullable=False, index=True)
    dimension = Column(String(200), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    levels = Column(JSON, nullable=False, default=list)
    sort_order = Column(Integer, nullable=False, default=0)

    # Relationships
    rubric = relationship("Rubric", back_populates="items")

    def __repr__(self):
        return f"<RubricItem(dimension={self.dimension}, weight={self.weight})>"
