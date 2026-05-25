"""Role model."""

from sqlalchemy import Column, String, JSON

from app.db.base import Base, CommonMixin


class Role(Base, CommonMixin):
    __tablename__ = "roles"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    permissions = Column(JSON, nullable=False, default=list)

    def __repr__(self):
        return f"<Role(code={self.code}, name={self.name})>"
