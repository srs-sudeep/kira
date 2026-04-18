"""Repository for reservation_notes — append-only."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation_note import ReservationNote


class NoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_for_reservation(self, reservation_id: uuid.UUID) -> list[ReservationNote]:
        rows = (
            (
                await self._s.execute(
                    select(ReservationNote)
                    .where(ReservationNote.reservation_id == reservation_id)
                    .order_by(ReservationNote.created_at)
                )
            )
            .scalars()
            .all()
        )
        return list(rows)

    async def create(
        self,
        reservation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> ReservationNote:
        note = ReservationNote(
            reservation_id=reservation_id,
            user_id=user_id,
            content=content,
        )
        self._s.add(note)
        await self._s.flush()
        await self._s.refresh(note)
        return note
