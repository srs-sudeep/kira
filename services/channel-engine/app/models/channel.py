"""Channel ORM model — represents a connected OTA (Booking.com, Expedia, etc.)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Channel(Base):
    __tablename__ = "channels"
    __table_args__ = (Index("idx_channel_ota_active", "ota_code", "is_active"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ota_code: Mapped[str] = mapped_column(String(30), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # AES-256-GCM encrypted JSON blob containing API credentials
    credentials_ref: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending_certification"
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Tracks consecutive failures for the circuit breaker
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    mappings: Mapped[list["ChannelMapping"]] = relationship(  # noqa: F821
        "ChannelMapping", back_populates="channel", cascade="all, delete-orphan"
    )
    sync_logs: Mapped[list["SyncLog"]] = relationship(  # noqa: F821
        "SyncLog", back_populates="channel", cascade="all, delete-orphan"
    )
