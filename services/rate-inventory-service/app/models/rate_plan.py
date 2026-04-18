"""ORM model for rate_plans (tenant schema)."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RatePlan(Base, TimestampMixin):
    __tablename__ = "rate_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    cancellation_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    deposit_policy: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Self-referential derived-rate FK
    derived_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rate_plans.id"),
        nullable=True,
    )
    derived_type: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,  # 'fixed' | 'percentage'
    )
    derived_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    min_los: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_los: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    room_type: Mapped["RoomType"] = relationship(  # noqa: F821
        "RoomType", back_populates="rate_plans"
    )
    # Children derived from this plan
    derived_plans: Mapped[list["RatePlan"]] = relationship(
        "RatePlan",
        foreign_keys=[derived_from_id],
        back_populates="parent_plan",
    )
    parent_plan: Mapped["RatePlan | None"] = relationship(
        "RatePlan",
        foreign_keys=[derived_from_id],
        back_populates="derived_plans",
        remote_side=[id],
    )
