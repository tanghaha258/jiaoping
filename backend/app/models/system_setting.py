"""SystemSetting model."""

from sqlalchemy import Column, String, JSON

from app.db.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False, default=dict)
    description = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<SystemSetting(key={self.key})>"
