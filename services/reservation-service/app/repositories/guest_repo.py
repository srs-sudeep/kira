"""Repository for guest_profiles."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_profile import GuestProfile


class GuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, guest_id: uuid.UUID) -> GuestProfile | None:
        return (await self._s.execute(select(GuestProfile).where(GuestProfile.id == guest_id))).scalar_one_or_none()

    async def get_by_email_hash(self, email_hash: str) -> GuestProfile | None:
        """Return the most-recently-created guest with this email hash."""
        return (
            await self._s.execute(
                select(GuestProfile)
                .where(GuestProfile.email_hash == email_hash)
                .order_by(GuestProfile.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def list_by_email_hash(self, email_hash: str) -> list[GuestProfile]:
        rows = (
            (await self._s.execute(select(GuestProfile).where(GuestProfile.email_hash == email_hash))).scalars().all()
        )
        return list(rows)

    async def create(
        self,
        *,
        first_name: str,
        last_name: str,
        email_encrypted: bytes | None,
        phone_encrypted: bytes | None,
        email_hash: str | None,
        nationality: str | None,
        preferences: dict,
    ) -> GuestProfile:
        guest = GuestProfile(
            first_name=first_name,
            last_name=last_name,
            email=email_encrypted,
            phone=phone_encrypted,
            email_hash=email_hash,
            nationality=nationality,
            preferences=preferences,
        )
        self._s.add(guest)
        await self._s.flush()
        await self._s.refresh(guest)
        return guest

    async def update(self, guest: GuestProfile, **kwargs) -> GuestProfile:
        for k, v in kwargs.items():
            setattr(guest, k, v)
        await self._s.flush()
        await self._s.refresh(guest)
        return guest
