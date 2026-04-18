"""ORM model for room_types (tenant schema)."""

import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RoomType(Base, TimestampMixin):
    __tablename__ = "room_types"
    # No schema= — search_path is set per-request by tenant middleware

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_occupancy: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    default_occupancy: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    bedding_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amenities: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    images: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    physical_inventory: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    rate_plans: Mapped[list["RatePlan"]] = relationship(  # noqa: F821
        "RatePlan", back_populates="room_type", cascade="all, delete-orphan"
    )
