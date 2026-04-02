"""SyncLog — immutable record of every ARI push / booking pull attempt."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SyncLog(Base):
    __tablename__ = "sync_logs"
    __table_args__ = (Index("idx_sync_channel_ts", "channel_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    # "ari_push" | "booking_pull" | "booking_push" | "error"
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # "outbound" | "inbound"
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # "success" | "failed" | "retrying"
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    channel: Mapped["Channel"] = relationship("Channel", back_populates="sync_logs")  # noqa: F821
