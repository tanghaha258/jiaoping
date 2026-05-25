"""User model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class User(Base, CommonMixin):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="student")
    school_id = Column(CHAR(36), ForeignKey("schools.id"), nullable=True)
    class_id = Column(CHAR(36), ForeignKey("classes.id"), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    school = relationship("School", backref="users", foreign_keys=[school_id])
    student_class = relationship("Class", backref="students", foreign_keys=[class_id])

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
