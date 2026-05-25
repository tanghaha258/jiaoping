"""Subject model."""

from sqlalchemy import Column, String

from app.db.base import Base, CommonMixin


class Subject(Base, CommonMixin):
    __tablename__ = "subjects"

    name = Column(String(100), nullable=False, unique=True)
    stage = Column(String(50), nullable=False, default="junior_high")

    def __repr__(self):
        return f"<Subject(name={self.name}, stage={self.stage})>"
