"""Shared declarative base, timestamp mixin, and soft-delete mixin."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = ["Base", "TimestampMixin", "SoftDeleteMixin"]


class TimestampMixin:
    """Adds created_at / updated_at to any ORM model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds deleted_at for soft-delete semantics.

    A row is considered deleted when deleted_at is not None.
    Queries must add a `WHERE deleted_at IS NULL` filter explicitly.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
