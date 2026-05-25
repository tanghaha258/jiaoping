"""Resource model."""

from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Resource(Base, CommonMixin):
    __tablename__ = "resources"

    school_id = Column(CHAR(36), ForeignKey("schools.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    resource_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=True)
    url = Column(String(500), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    visibility = Column(String(20), nullable=False, default="school")
    status = Column(String(20), nullable=False, default="draft")

    # Relationships
    school = relationship("School", backref="resources")

    def __repr__(self):
        return f"<Resource(title={self.title}, type={self.resource_type})>"
