"""Shared SQLAlchemy base and timestamp mixin for rate-inventory-service."""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = ["Base", "TimestampMixin"]


class TimestampMixin:
    """Adds created_at / updated_at columns with automatic server-side defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
