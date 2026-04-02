"""ORM model for ari_snapshots (tenant schema) — no created_at by design."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ARISnapshot(Base):
    __tablename__ = "ari_snapshots"
    __table_args__ = (
        UniqueConstraint("room_type_id", "rate_plan_id", "date", name="uq_ari"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_types.id"),
        nullable=False,
    )
    rate_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rate_plans.id"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    available_rooms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rate_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cta_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ctd_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_los: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_los: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    overbooking_buffer: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # No created_at — matches the DB schema (ari_snapshots is a mutable snapshot)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
