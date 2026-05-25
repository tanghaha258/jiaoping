"""SQLAlchemy declarative base and common mixins."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Abstract base class for all models."""
    pass


def generate_uuid():
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Mixin adding created_at and updated_at columns."""

    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin adding soft delete support via deleted_at."""

    deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)


class UUIDPrimaryKeyMixin:
    """Mixin adding a UUID primary key."""

    id = Column(
        CHAR(36),
        primary_key=True,
        default=generate_uuid,
        index=True,
    )


class CommonMixin(TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin):
    """Combined mixin with id (UUID), created_at, updated_at, deleted_at."""
    pass
