"""ORM model for guest_profiles (tenant schema).

PII fields (email, phone) are stored as AES-256-GCM encrypted BYTEA.
email_hash (SHA-256) is the only lookupable identifier for email searches.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GuestProfile(Base):
    __tablename__ = "guest_profiles"
    __table_args__ = (Index("idx_guest_email", "email_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # AES-256-GCM encrypted bytes — None if not provided
    email: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    phone: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    # SHA-256(lower(email)) for lookups without decryption
    email_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(3), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reservations: Mapped[list["Reservation"]] = relationship(  # noqa: F821
        "Reservation", back_populates="guest_profile"
    )
