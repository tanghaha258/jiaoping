"""Region model."""

from sqlalchemy import Column, String

from app.db.base import Base, CommonMixin


class Region(Base, CommonMixin):
    __tablename__ = "regions"

    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Region(name={self.name}, code={self.code})>"
