"""Repository for reservations — inbox queries, CRUD, duplicate detection."""

import random
import string
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.guest_profile import GuestProfile
from app.models.reservation import Reservation
from app.schemas.reservation import InboxFilters

_SORT_COLS = {
    "check_in": Reservation.check_in,
    "created_at": Reservation.created_at,
    "total_amount": Reservation.total_amount,
    "confirmation_number": Reservation.confirmation_number,
}
_TERMINAL_STATUSES = ("cancelled", "no_show", "checked_out")


def _generate_confirmation_number() -> str:
    chars = string.ascii_uppercase + string.digits
    return "RES-" + "".join(random.choices(chars, k=6))


class ReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, reservation_id: uuid.UUID, *, load_relations: bool = False) -> Reservation | None:
        stmt = select(Reservation).where(Reservation.id == reservation_id)
        if load_relations:
            stmt = stmt.options(
                selectinload(Reservation.guest_profile),
                selectinload(Reservation.notes),
            )
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def get_by_confirmation(self, confirmation_number: str) -> Reservation | None:
        return (
            await self._s.execute(select(Reservation).where(Reservation.confirmation_number == confirmation_number))
        ).scalar_one_or_none()

    async def _unique_confirmation_number(self) -> str:
        for _ in range(10):
            cn = _generate_confirmation_number()
            existing = await self.get_by_confirmation(cn)
            if existing is None:
                return cn
        raise RuntimeError("Failed to generate unique confirmation number after 10 attempts.")

    async def create(
        self,
        *,
        guest_profile_id: uuid.UUID,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        check_in: date,
        check_out: date,
        source: str,
        channel_id: uuid.UUID | None,
        channel_reservation_id: str | None,
        adults: int,
        children: int,
        total_amount: Decimal,
        currency: str,
        cancellation_policy: dict | None,
        special_requests: str | None,
    ) -> Reservation:
        cn = await self._unique_confirmation_number()
        res = Reservation(
            confirmation_number=cn,
            guest_profile_id=guest_profile_id,
            room_type_id=room_type_id,
            rate_plan_id=rate_plan_id,
            check_in=check_in,
            check_out=check_out,
            source=source,
            channel_id=channel_id,
            channel_reservation_id=channel_reservation_id,
            adults=adults,
            children=children,
            total_amount=total_amount,
            currency=currency,
            cancellation_policy=cancellation_policy,
            special_requests=special_requests,
            status="confirmed",
        )
        self._s.add(res)
        await self._s.flush()
        await self._s.refresh(res)
        return res

    async def update(self, reservation: Reservation, **kwargs) -> Reservation:
        for k, v in kwargs.items():
            setattr(reservation, k, v)
        await self._s.flush()
        await self._s.refresh(reservation)
        return reservation

    async def get_inbox(self, filters: InboxFilters) -> tuple[list[Reservation], int]:
        stmt = (
            select(Reservation)
            .join(GuestProfile, Reservation.guest_profile_id == GuestProfile.id)
            .options(selectinload(Reservation.guest_profile))
        )

        if filters.status:
            stmt = stmt.where(Reservation.status.in_(filters.status))
        if filters.source:
            stmt = stmt.where(Reservation.source.in_(filters.source))
        if filters.channel_id:
            stmt = stmt.where(Reservation.channel_id == filters.channel_id)
        if filters.check_in_from:
            stmt = stmt.where(Reservation.check_in >= filters.check_in_from)
        if filters.check_in_to:
            stmt = stmt.where(Reservation.check_in <= filters.check_in_to)
        if filters.check_out_from:
            stmt = stmt.where(Reservation.check_out >= filters.check_out_from)
        if filters.check_out_to:
            stmt = stmt.where(Reservation.check_out <= filters.check_out_to)
        if filters.guest_query:
            q = f"%{filters.guest_query}%"
            stmt = stmt.where(
                or_(
                    GuestProfile.first_name.ilike(q),
                    GuestProfile.last_name.ilike(q),
                    GuestProfile.email_hash == filters.guest_query,
                )
            )

        sort_col = _SORT_COLS.get(filters.sort_by, Reservation.created_at)
        stmt = stmt.order_by(asc(sort_col) if filters.sort_dir == "asc" else desc(sort_col))

        total = (await self._s.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
        rows = (
            (await self._s.execute(stmt.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)))
            .scalars()
            .all()
        )
        return list(rows), total

    async def find_duplicates(
        self,
        email_hash: str,
        room_type_id: uuid.UUID,
        check_in: date,
        check_out: date,
        exclude_id: uuid.UUID | None = None,
    ) -> list[Reservation]:
        """Return active reservations with overlapping dates for the same guest+room."""
        stmt = (
            select(Reservation)
            .join(GuestProfile, Reservation.guest_profile_id == GuestProfile.id)
            .options(selectinload(Reservation.guest_profile))
            .where(
                GuestProfile.email_hash == email_hash,
                Reservation.room_type_id == room_type_id,
                Reservation.status.notin_(list(_TERMINAL_STATUSES)),
                # Overlap: existing check_in < new check_out AND existing check_out > new check_in
                Reservation.check_in < check_out,
                Reservation.check_out > check_in,
            )
        )
        if exclude_id:
            stmt = stmt.where(Reservation.id != exclude_id)
        rows = (await self._s.execute(stmt)).scalars().all()
        return list(rows)

    async def find_all_duplicates(self) -> list[tuple[str, uuid.UUID, list[Reservation]]]:
        """
        Return groups of (email_hash, room_type_id, [reservations]) where
        the same guest has overlapping active reservations in the same room type.
        """
        from sqlalchemy import text

        # Raw query for readability; returns (reservation_id, email_hash, room_type_id)
        raw = text("""
            SELECT DISTINCT r1.id
            FROM reservations r1
            JOIN guest_profiles g1 ON r1.guest_profile_id = g1.id
            JOIN reservations r2 ON r1.room_type_id = r2.room_type_id
            JOIN guest_profiles g2 ON r2.guest_profile_id = g2.id
            WHERE r1.id != r2.id
              AND g1.email_hash IS NOT NULL
              AND g1.email_hash = g2.email_hash
              AND r1.status NOT IN ('cancelled','no_show','checked_out')
              AND r2.status NOT IN ('cancelled','no_show','checked_out')
              AND r1.check_in < r2.check_out
              AND r1.check_out > r2.check_in
        """)
        dup_ids_result = await self._s.execute(raw)
        dup_ids = [row[0] for row in dup_ids_result]
        if not dup_ids:
            return []

        rows = (
            (
                await self._s.execute(
                    select(Reservation)
                    .options(selectinload(Reservation.guest_profile))
                    .where(Reservation.id.in_(dup_ids))
                    .order_by(Reservation.check_in)
                )
            )
            .scalars()
            .all()
        )

        # Group by (email_hash, room_type_id)
        groups: dict[tuple[str, uuid.UUID], list[Reservation]] = {}
        for res in rows:
            key = (res.guest_profile.email_hash or "", res.room_type_id)
            groups.setdefault(key, []).append(res)
        return [(k[0], k[1], v) for k, v in groups.items()]
