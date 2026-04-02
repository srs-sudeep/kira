"""Reservation business logic: create, modify, cancel, notes, duplicates."""
import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ari_client import AvailabilityResult, ari_client
from app.core.crypto import decrypt_pii, encrypt_pii, hash_email
from app.events.producer import kafka_producer
from app.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.reservation import Reservation
from app.repositories.guest_repo import GuestRepository
from app.repositories.note_repo import NoteRepository
from app.repositories.reservation_repo import ReservationRepository
from app.schemas.guest import GuestBrief, GuestCreate, GuestResponse
from app.schemas.note import NoteCreate, NoteResponse
from app.schemas.reservation import (
    DuplicateGroup,
    DuplicatesResponse,
    InboxFilters,
    ReservationBrief,
    ReservationCancel,
    ReservationCreate,
    ReservationDetail,
    ReservationInboxResponse,
    ReservationModify,
    ReservationStatusUpdate,
)
from app.tasks.email_tasks import send_booking_confirmation, send_cancellation_notice, send_modification_notice

logger = structlog.get_logger(__name__)

_MODIFIABLE_STATUSES = ("confirmed", "modified")
_CANCELLABLE_STATUSES = ("confirmed", "modified", "checked_in")


class ReservationService:
    def __init__(self, session: AsyncSession) -> None:
        self._res_repo = ReservationRepository(session)
        self._guest_repo = GuestRepository(session)
        self._note_repo = NoteRepository(session)

    # ── Helper: build response objects ───────────────────────────────────────

    def _guest_brief(self, guest) -> GuestBrief:
        return GuestBrief(id=guest.id, first_name=guest.first_name, last_name=guest.last_name)

    def _guest_response(self, guest) -> GuestResponse:
        email = None
        phone = None
        try:
            if guest.email:
                email = decrypt_pii(guest.email)
        except Exception:
            pass
        try:
            if guest.phone:
                phone = decrypt_pii(guest.phone)
        except Exception:
            pass
        return GuestResponse(
            id=guest.id,
            first_name=guest.first_name,
            last_name=guest.last_name,
            email=email,
            phone=phone,
            nationality=guest.nationality,
            preferences=guest.preferences or {},
            created_at=guest.created_at,
            updated_at=guest.updated_at,
        )

    def _res_brief(self, res: Reservation) -> ReservationBrief:
        return ReservationBrief(
            id=res.id,
            confirmation_number=res.confirmation_number,
            source=res.source,
            channel_id=res.channel_id,
            room_type_id=res.room_type_id,
            rate_plan_id=res.rate_plan_id,
            check_in=res.check_in,
            check_out=res.check_out,
            nights=res.nights,
            adults=res.adults,
            children=res.children,
            total_amount=res.total_amount,
            currency=res.currency,
            status=res.status,
            special_requests=res.special_requests,
            guest=self._guest_brief(res.guest_profile),
            created_at=res.created_at,
        )

    def _res_detail(self, res: Reservation) -> ReservationDetail:
        return ReservationDetail(
            id=res.id,
            confirmation_number=res.confirmation_number,
            source=res.source,
            channel_id=res.channel_id,
            channel_reservation_id=res.channel_reservation_id,
            room_type_id=res.room_type_id,
            rate_plan_id=res.rate_plan_id,
            check_in=res.check_in,
            check_out=res.check_out,
            nights=res.nights,
            adults=res.adults,
            children=res.children,
            total_amount=res.total_amount,
            currency=res.currency,
            status=res.status,
            cancellation_policy=res.cancellation_policy,
            cancelled_at=res.cancelled_at,
            cancellation_reason=res.cancellation_reason,
            special_requests=res.special_requests,
            guest=self._guest_response(res.guest_profile),
            notes=[NoteResponse.model_validate(n) for n in res.notes],
            created_at=res.created_at,
            updated_at=res.updated_at,
        )

    # ── Inbox ─────────────────────────────────────────────────────────────────

    async def get_inbox(self, filters: InboxFilters) -> ReservationInboxResponse:
        rows, total = await self._res_repo.get_inbox(filters)
        return ReservationInboxResponse(
            items=[self._res_brief(r) for r in rows],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=max(1, math.ceil(total / filters.page_size)),
        )

    # ── Detail ────────────────────────────────────────────────────────────────

    async def get_detail(self, reservation_id: uuid.UUID) -> ReservationDetail:
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        if res is None:
            raise NotFoundError("Reservation", str(reservation_id))
        return self._res_detail(res)

    # ── Create (manual booking) ───────────────────────────────────────────────

    async def create_reservation(
        self,
        req: ReservationCreate,
        *,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        token: str,
    ) -> ReservationDetail:
        # 1. Availability check
        avail = await ari_client.check_availability(
            req.room_type_id, req.rate_plan_id,
            req.check_in, req.check_out,
            token, tenant_id,
        )
        if not avail.available:
            raise ValidationError(
                f"Room not available: {avail.reason or 'no inventory for requested dates'}"
            )

        # 2. Resolve or create guest profile
        email_plain = req.guest.email
        email_hash_val = hash_email(email_plain) if email_plain else None
        email_enc = encrypt_pii(email_plain) if email_plain else None
        phone_enc = encrypt_pii(req.guest.phone) if req.guest.phone else None

        guest = None
        if email_hash_val:
            guest = await self._guest_repo.get_by_email_hash(email_hash_val)
        if guest is None:
            guest = await self._guest_repo.create(
                first_name=req.guest.first_name,
                last_name=req.guest.last_name,
                email_encrypted=email_enc,
                phone_encrypted=phone_enc,
                email_hash=email_hash_val,
                nationality=req.guest.nationality,
                preferences=req.guest.preferences,
            )

        # 3. Create reservation
        res = await self._res_repo.create(
            guest_profile_id=guest.id,
            room_type_id=req.room_type_id,
            rate_plan_id=req.rate_plan_id,
            check_in=req.check_in,
            check_out=req.check_out,
            source=req.source,
            channel_id=req.channel_id,
            channel_reservation_id=None,
            adults=req.adults,
            children=req.children,
            total_amount=avail.total_amount,
            currency="INR",
            cancellation_policy=None,
            special_requests=req.special_requests,
        )

        # 4. Decrement ARI (best-effort — reservation is committed regardless)
        ok = await ari_client.adjust_inventory(
            req.room_type_id, req.rate_plan_id,
            req.check_in, req.check_out,
            delta=-1, token=token, tenant_id=tenant_id,
        )
        if not ok:
            logger.warning(
                "ari_decrement_failed",
                reservation_id=str(res.id),
                room_type_id=str(req.room_type_id),
            )

        # 5. Publish Kafka event
        await kafka_producer.reservation_created(
            reservation_id=res.id,
            tenant_id=tenant_id,
            confirmation_number=res.confirmation_number,
            source=res.source,
            room_type_id=res.room_type_id,
            rate_plan_id=res.rate_plan_id,
            check_in=res.check_in,
            check_out=res.check_out,
            total_amount=res.total_amount,
            guest_id=guest.id,
        )

        # 6. Confirmation email (if guest email available)
        if email_plain:
            send_booking_confirmation.delay(
                to_email=email_plain,
                guest_name=f"{guest.first_name} {guest.last_name}",
                confirmation_number=res.confirmation_number,
                hotel_name="Your Property",
                check_in=req.check_in.isoformat(),
                check_out=req.check_out.isoformat(),
                nights=res.nights,
                total_amount=str(res.total_amount),
                currency=res.currency,
            )

        logger.info(
            "reservation_created",
            id=str(res.id),
            confirmation=res.confirmation_number,
            source=res.source,
        )
        # Re-load with relations for the detail response
        res = await self._res_repo.get_by_id(res.id, load_relations=True)
        return self._res_detail(res)

    # ── Modify ────────────────────────────────────────────────────────────────

    async def modify_reservation(
        self,
        reservation_id: uuid.UUID,
        req: ReservationModify,
        *,
        tenant_id: uuid.UUID,
        token: str,
    ) -> ReservationDetail:
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        if res is None:
            raise NotFoundError("Reservation", str(reservation_id))
        if res.status not in _MODIFIABLE_STATUSES:
            raise ValidationError(
                f"Cannot modify a reservation with status '{res.status}'."
            )

        updates = req.model_dump(exclude_none=True)
        if not updates:
            return self._res_detail(res)

        new_check_in = req.check_in or res.check_in
        new_check_out = req.check_out or res.check_out
        new_room_type = req.room_type_id or res.room_type_id
        new_rate_plan = req.rate_plan_id or res.rate_plan_id
        dates_changed = (new_check_in != res.check_in or new_check_out != res.check_out
                         or new_room_type != res.room_type_id or new_rate_plan != res.rate_plan_id)

        new_total = res.total_amount
        if dates_changed:
            avail = await ari_client.check_availability(
                new_room_type, new_rate_plan, new_check_in, new_check_out, token, tenant_id
            )
            if not avail.available:
                raise ValidationError(
                    f"New dates/room not available: {avail.reason}"
                )
            # Release old inventory, book new
            await ari_client.adjust_inventory(
                res.room_type_id, res.rate_plan_id,
                res.check_in, res.check_out,
                delta=+1, token=token, tenant_id=tenant_id,
            )
            await ari_client.adjust_inventory(
                new_room_type, new_rate_plan,
                new_check_in, new_check_out,
                delta=-1, token=token, tenant_id=tenant_id,
            )
            new_total = avail.total_amount
            updates["total_amount"] = new_total
            updates["check_in"] = new_check_in
            updates["check_out"] = new_check_out
            updates["room_type_id"] = new_room_type
            updates["rate_plan_id"] = new_rate_plan

        updates["status"] = "modified"
        changed_fields = list(updates.keys())
        res = await self._res_repo.update(res, **updates)

        await kafka_producer.reservation_modified(
            reservation_id=res.id, tenant_id=tenant_id, changed_fields=changed_fields
        )

        # Modification email (best-effort)
        try:
            if res.guest_profile.email:
                email_plain = decrypt_pii(res.guest_profile.email)
                send_modification_notice.delay(
                    to_email=email_plain,
                    guest_name=f"{res.guest_profile.first_name} {res.guest_profile.last_name}",
                    confirmation_number=res.confirmation_number,
                    changes=", ".join(changed_fields),
                )
        except Exception:
            pass

        logger.info("reservation_modified", id=str(reservation_id), fields=changed_fields)
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        return self._res_detail(res)

    # ── Cancel ────────────────────────────────────────────────────────────────

    async def cancel_reservation(
        self,
        reservation_id: uuid.UUID,
        req: ReservationCancel,
        *,
        tenant_id: uuid.UUID,
        token: str,
    ) -> ReservationDetail:
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        if res is None:
            raise NotFoundError("Reservation", str(reservation_id))
        if res.status not in _CANCELLABLE_STATUSES:
            raise ValidationError(
                f"Cannot cancel a reservation with status '{res.status}'."
            )

        now = datetime.now(UTC)
        updates = {
            "status": "cancelled",
            "cancelled_at": now,
            "cancellation_reason": req.cancellation_reason,
        }
        res = await self._res_repo.update(res, **updates)

        # Release inventory (best-effort)
        await ari_client.adjust_inventory(
            res.room_type_id, res.rate_plan_id,
            res.check_in, res.check_out,
            delta=+1, token=token, tenant_id=tenant_id,
        )

        await kafka_producer.reservation_cancelled(
            reservation_id=res.id,
            tenant_id=tenant_id,
            confirmation_number=res.confirmation_number,
            cancellation_reason=req.cancellation_reason,
            room_type_id=res.room_type_id,
            rate_plan_id=res.rate_plan_id,
            check_in=res.check_in,
            check_out=res.check_out,
        )

        # Cancellation email (best-effort)
        try:
            if res.guest_profile.email:
                email_plain = decrypt_pii(res.guest_profile.email)
                send_cancellation_notice.delay(
                    to_email=email_plain,
                    guest_name=f"{res.guest_profile.first_name} {res.guest_profile.last_name}",
                    confirmation_number=res.confirmation_number,
                    reason=req.cancellation_reason,
                )
        except Exception:
            pass

        logger.info("reservation_cancelled", id=str(reservation_id))
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        return self._res_detail(res)

    # ── Status transition (check-in, check-out, no-show) ─────────────────────

    async def update_status(
        self,
        reservation_id: uuid.UUID,
        req: ReservationStatusUpdate,
    ) -> ReservationDetail:
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        if res is None:
            raise NotFoundError("Reservation", str(reservation_id))

        _allowed_transitions = {
            "no_show": ("confirmed", "modified"),
            "checked_in": ("confirmed", "modified"),
            "checked_out": ("checked_in",),
        }
        allowed_from = _allowed_transitions.get(req.status, ())
        if res.status not in allowed_from:
            raise ValidationError(
                f"Cannot transition from '{res.status}' to '{req.status}'."
            )

        res = await self._res_repo.update(res, status=req.status)
        logger.info("reservation_status_updated", id=str(reservation_id), status=req.status)
        res = await self._res_repo.get_by_id(reservation_id, load_relations=True)
        return self._res_detail(res)

    # ── Notes ─────────────────────────────────────────────────────────────────

    async def add_note(
        self,
        reservation_id: uuid.UUID,
        req: NoteCreate,
        user_id: uuid.UUID,
    ) -> NoteResponse:
        res = await self._res_repo.get_by_id(reservation_id)
        if res is None:
            raise NotFoundError("Reservation", str(reservation_id))
        note = await self._note_repo.create(reservation_id, user_id, req.content)
        return NoteResponse.model_validate(note)

    # ── Duplicate detection ───────────────────────────────────────────────────

    async def get_duplicates(self) -> DuplicatesResponse:
        groups_raw = await self._res_repo.find_all_duplicates()
        groups = [
            DuplicateGroup(
                email_hash=email_hash,
                room_type_id=room_type_id,
                reservations=[self._res_brief(r) for r in reservations],
            )
            for email_hash, room_type_id, reservations in groups_raw
        ]
        total = sum(len(g.reservations) for g in groups)
        return DuplicatesResponse(groups=groups, total_duplicates=total)
