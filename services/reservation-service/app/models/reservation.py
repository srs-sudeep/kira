"""ORM model for reservations (tenant schema)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        Index("idx_res_dates", "check_in", "check_out"),
        Index("idx_res_status", "status"),
        Index("idx_res_source", "source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    confirmation_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    channel_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    room_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rate_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    # Computed column — PostgreSQL calculates (check_out - check_in)
    nights: Mapped[int] = mapped_column(
        Integer,
        Computed("check_out - check_in", persisted=True),
        nullable=False,
    )
    guest_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guest_profiles.id"),
        nullable=False,
    )
    adults: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    cancellation_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel_reservation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    guest_profile: Mapped["GuestProfile"] = relationship(  # noqa: F821
        "GuestProfile", back_populates="reservations"
    )
    notes: Mapped[list["ReservationNote"]] = relationship(  # noqa: F821
        "ReservationNote",
        back_populates="reservation",
        cascade="all, delete-orphan",
        order_by="ReservationNote.created_at",
    )
