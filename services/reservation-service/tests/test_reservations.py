"""Tests for reservation CRUD, status transitions, notes, and duplicate detection."""
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError, ValidationError
from app.schemas.note import NoteCreate
from app.schemas.reservation import (
    InboxFilters,
    ReservationCancel,
    ReservationCreate,
    ReservationModify,
    ReservationStatusUpdate,
)
from app.schemas.guest import GuestCreate
from app.services.reservation_service import ReservationService
from tests.conftest import (
    FAKE_TENANT_ID,
    FAKE_TOKEN,
    FAKE_USER_ID,
    make_guest,
    make_reservation,
)

TODAY = date(2026, 6, 1)
TOMORROW = date(2026, 6, 2)
DAY3 = date(2026, 6, 3)
DAY5 = date(2026, 6, 5)

ROOM_TYPE_ID = uuid.uuid4()
RATE_PLAN_ID = uuid.uuid4()


def _avail_ok(total: Decimal = Decimal("10000.00")):
    from app.core.ari_client import AvailabilityResult
    return AvailabilityResult(available=True, total_amount=total, reason=None)


def _avail_no():
    from app.core.ari_client import AvailabilityResult
    return AvailabilityResult(available=False, total_amount=Decimal("0"), reason="No rooms")


class TestGetInbox:
    async def test_returns_empty_when_no_reservations(self, db: AsyncSession):
        svc = ReservationService(db)
        result = await svc.get_inbox(InboxFilters())
        assert result.total == 0
        assert result.items == []

    async def test_returns_paginated_results(self, db: AsyncSession):
        guest = await make_guest(db)
        await make_reservation(db, guest.id, room_type_id=ROOM_TYPE_ID, rate_plan_id=RATE_PLAN_ID)
        await make_reservation(db, guest.id, room_type_id=ROOM_TYPE_ID, rate_plan_id=RATE_PLAN_ID)
        await db.commit()

        svc = ReservationService(db)
        result = await svc.get_inbox(InboxFilters(page=1, page_size=1))
        assert result.total == 2
        assert len(result.items) == 1
        assert result.pages == 2

    async def test_filters_by_status(self, db: AsyncSession):
        guest = await make_guest(db)
        await make_reservation(db, guest.id, status="confirmed")
        await make_reservation(db, guest.id, status="cancelled")
        await db.commit()

        svc = ReservationService(db)
        result = await svc.get_inbox(InboxFilters(status=["confirmed"]))
        assert result.total == 1
        assert result.items[0].status == "confirmed"

    async def test_filters_by_source(self, db: AsyncSession):
        guest = await make_guest(db)
        await make_reservation(db, guest.id, source="manual")
        await make_reservation(db, guest.id, source="booking_com")
        await db.commit()

        svc = ReservationService(db)
        result = await svc.get_inbox(InboxFilters(source=["manual"]))
        assert result.total == 1
        assert result.items[0].source == "manual"


class TestGetDetail:
    async def test_returns_detail_with_guest(self, db: AsyncSession):
        guest = await make_guest(db, first_name="Bob", last_name="Jones")
        res = await make_reservation(db, guest.id)
        await db.commit()

        svc = ReservationService(db)
        detail = await svc.get_detail(res.id)
        assert detail.id == res.id
        assert detail.guest.first_name == "Bob"
        assert detail.notes == []

    async def test_raises_not_found_for_unknown_id(self, db: AsyncSession):
        svc = ReservationService(db)
        with pytest.raises(NotFoundError):
            await svc.get_detail(uuid.uuid4())


class TestCreateReservation:
    def _make_req(self, room_type_id=None, rate_plan_id=None):
        return ReservationCreate(
            room_type_id=room_type_id or ROOM_TYPE_ID,
            rate_plan_id=rate_plan_id or RATE_PLAN_ID,
            check_in=TODAY,
            check_out=DAY3,
            source="manual",
            adults=2,
            children=0,
            guest=GuestCreate(
                first_name="Carol",
                last_name="White",
                email="carol@example.com",
                phone="+919900000001",
            ),
        )

    async def test_creates_reservation_when_available(self, db: AsyncSession, mock_kafka):
        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_ok())
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.create_reservation(
                self._make_req(),
                actor_id=FAKE_USER_ID,
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        assert detail.confirmation_number.startswith("RES-")
        assert detail.status == "confirmed"
        assert detail.guest.first_name == "Carol"
        assert detail.total_amount == Decimal("10000.00")
        mock_kafka.reservation_created.assert_awaited_once()

    async def test_raises_when_room_unavailable(self, db: AsyncSession):
        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_no())

            svc = ReservationService(db)
            with pytest.raises(ValidationError, match="not available"):
                await svc.create_reservation(
                    self._make_req(),
                    actor_id=FAKE_USER_ID,
                    tenant_id=FAKE_TENANT_ID,
                    token=FAKE_TOKEN,
                )

    async def test_reuses_existing_guest_by_email(self, db: AsyncSession):
        from app.core.crypto import encrypt_pii, hash_email

        email = "carol@example.com"
        email_hash = hash_email(email)
        existing_guest = await make_guest(
            db,
            first_name="Carol",
            last_name="White",
            email_hash=email_hash,
            email_encrypted=encrypt_pii(email),
        )
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_ok())
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.create_reservation(
                self._make_req(),
                actor_id=FAKE_USER_ID,
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        # Should reuse same guest profile
        assert detail.guest.id == existing_guest.id

    async def test_ari_decrement_failure_does_not_rollback(self, db: AsyncSession, mock_kafka):
        """Reservation is committed even if ARI decrement fails."""
        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_ok())
            mock_ari.adjust_inventory = AsyncMock(return_value=False)  # decrement fails

            svc = ReservationService(db)
            detail = await svc.create_reservation(
                self._make_req(),
                actor_id=FAKE_USER_ID,
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        # Reservation was still created
        assert detail.id is not None


class TestModifyReservation:
    async def test_modify_dates_checks_new_availability(self, db: AsyncSession, mock_kafka):
        guest = await make_guest(db)
        res = await make_reservation(
            db, guest.id,
            room_type_id=ROOM_TYPE_ID,
            rate_plan_id=RATE_PLAN_ID,
            check_in=TODAY,
            check_out=TOMORROW,
        )
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_ok(Decimal("15000.00")))
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.modify_reservation(
                res.id,
                ReservationModify(check_in=TODAY, check_out=DAY5),
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        assert detail.status == "modified"
        assert detail.check_out == DAY5
        assert detail.total_amount == Decimal("15000.00")
        mock_kafka.reservation_modified.assert_awaited_once()

    async def test_modify_non_date_fields_skips_availability(self, db: AsyncSession, mock_kafka):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="confirmed")
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_ok())
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.modify_reservation(
                res.id,
                ReservationModify(adults=3),
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        assert detail.adults == 3
        # No availability check needed for non-date/room changes
        mock_ari.check_availability.assert_not_called()

    async def test_modify_cancelled_raises(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="cancelled")
        await db.commit()

        with patch("app.services.reservation_service.ari_client"):
            svc = ReservationService(db)
            with pytest.raises(ValidationError, match="Cannot modify"):
                await svc.modify_reservation(
                    res.id,
                    ReservationModify(adults=2),
                    tenant_id=FAKE_TENANT_ID,
                    token=FAKE_TOKEN,
                )

    async def test_modify_new_dates_unavailable_raises(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, check_in=TODAY, check_out=TOMORROW)
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_no())
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            with pytest.raises(ValidationError, match="not available"):
                await svc.modify_reservation(
                    res.id,
                    ReservationModify(check_out=DAY5),
                    tenant_id=FAKE_TENANT_ID,
                    token=FAKE_TOKEN,
                )

    async def test_modify_not_found_raises(self, db: AsyncSession):
        with patch("app.services.reservation_service.ari_client"):
            svc = ReservationService(db)
            with pytest.raises(NotFoundError):
                await svc.modify_reservation(
                    uuid.uuid4(),
                    ReservationModify(adults=1),
                    tenant_id=FAKE_TENANT_ID,
                    token=FAKE_TOKEN,
                )


class TestCancelReservation:
    async def test_cancel_confirmed_reservation(self, db: AsyncSession, mock_kafka):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="confirmed")
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.cancel_reservation(
                res.id,
                ReservationCancel(cancellation_reason="Guest request"),
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )

        assert detail.status == "cancelled"
        assert detail.cancellation_reason == "Guest request"
        assert detail.cancelled_at is not None
        mock_kafka.reservation_cancelled.assert_awaited_once()

    async def test_cancel_checked_in_allowed(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="checked_in")
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            svc = ReservationService(db)
            detail = await svc.cancel_reservation(
                res.id,
                ReservationCancel(cancellation_reason="Emergency"),
                tenant_id=FAKE_TENANT_ID,
                token=FAKE_TOKEN,
            )
        assert detail.status == "cancelled"

    async def test_cancel_already_cancelled_raises(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="cancelled")
        await db.commit()

        with patch("app.services.reservation_service.ari_client"):
            svc = ReservationService(db)
            with pytest.raises(ValidationError, match="Cannot cancel"):
                await svc.cancel_reservation(
                    res.id,
                    ReservationCancel(cancellation_reason="Duplicate"),
                    tenant_id=FAKE_TENANT_ID,
                    token=FAKE_TOKEN,
                )

    async def test_cancel_checked_out_raises(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="checked_out")
        await db.commit()

        with patch("app.services.reservation_service.ari_client"):
            svc = ReservationService(db)
            with pytest.raises(ValidationError, match="Cannot cancel"):
                await svc.cancel_reservation(
                    res.id,
                    ReservationCancel(cancellation_reason="Too late"),
                    tenant_id=FAKE_TENANT_ID,
                    token=FAKE_TOKEN,
                )


class TestStatusTransitions:
    @pytest.mark.parametrize("initial,target", [
        ("confirmed", "checked_in"),
        ("modified", "checked_in"),
        ("confirmed", "no_show"),
        ("modified", "no_show"),
        ("checked_in", "checked_out"),
    ])
    async def test_valid_transitions(self, db: AsyncSession, initial, target):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status=initial)
        await db.commit()

        svc = ReservationService(db)
        detail = await svc.update_status(res.id, ReservationStatusUpdate(status=target))
        assert detail.status == target

    @pytest.mark.parametrize("initial,target", [
        ("confirmed", "checked_out"),
        ("cancelled", "checked_in"),
        ("checked_out", "checked_in"),
        ("no_show", "checked_in"),
    ])
    async def test_invalid_transitions_raise(self, db: AsyncSession, initial, target):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status=initial)
        await db.commit()

        svc = ReservationService(db)
        with pytest.raises(ValidationError, match="Cannot transition"):
            await svc.update_status(res.id, ReservationStatusUpdate(status=target))


class TestNotes:
    async def test_add_note(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id)
        await db.commit()

        svc = ReservationService(db)
        note = await svc.add_note(res.id, NoteCreate(content="Early check-in requested."), FAKE_USER_ID)
        assert note.content == "Early check-in requested."
        assert note.user_id == FAKE_USER_ID

    async def test_add_note_to_nonexistent_reservation_raises(self, db: AsyncSession):
        svc = ReservationService(db)
        with pytest.raises(NotFoundError):
            await svc.add_note(uuid.uuid4(), NoteCreate(content="Test"), FAKE_USER_ID)

    async def test_notes_appear_in_detail(self, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id)
        await db.commit()

        svc = ReservationService(db)
        await svc.add_note(res.id, NoteCreate(content="Note 1"), FAKE_USER_ID)
        await svc.add_note(res.id, NoteCreate(content="Note 2"), FAKE_USER_ID)
        await db.commit()

        detail = await svc.get_detail(res.id)
        assert len(detail.notes) == 2
        assert detail.notes[0].content == "Note 1"


class TestDuplicates:
    async def test_no_duplicates_when_different_guests(self, db: AsyncSession):
        g1 = await make_guest(db, email_hash="hash_a")
        g2 = await make_guest(db, email_hash="hash_b")
        rt = uuid.uuid4()
        await make_reservation(db, g1.id, room_type_id=rt, check_in=TODAY, check_out=TOMORROW)
        await make_reservation(db, g2.id, room_type_id=rt, check_in=TODAY, check_out=TOMORROW)
        await db.commit()

        svc = ReservationService(db)
        result = await svc.get_duplicates()
        assert result.total_duplicates == 0

    async def test_detects_same_guest_same_room_overlapping(self, db: AsyncSession):
        guest = await make_guest(db, email_hash="hash_dup")
        rt = uuid.uuid4()
        rp = uuid.uuid4()
        await make_reservation(
            db, guest.id,
            room_type_id=rt, rate_plan_id=rp,
            check_in=TODAY, check_out=DAY3,
            status="confirmed",
        )
        await make_reservation(
            db, guest.id,
            room_type_id=rt, rate_plan_id=rp,
            check_in=TOMORROW, check_out=DAY5,
            status="confirmed",
        )
        await db.commit()

        svc = ReservationService(db)
        result = await svc.get_duplicates()
        assert result.total_duplicates >= 2
        assert len(result.groups) >= 1


class TestReservationRoutes:
    async def test_get_inbox_route(self, client, db: AsyncSession):
        guest = await make_guest(db)
        await make_reservation(db, guest.id)
        await db.commit()
        resp = await client.get("/api/v1/reservations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    async def test_get_detail_route_not_found(self, client):
        resp = await client.get(f"/api/v1/reservations/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_create_reservation_route(self, client, db: AsyncSession, mock_kafka):
        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.check_availability = AsyncMock(return_value=_avail_ok())
            mock_ari.adjust_inventory = AsyncMock(return_value=True)

            resp = await client.post(
                "/api/v1/reservations",
                json={
                    "room_type_id": str(ROOM_TYPE_ID),
                    "rate_plan_id": str(RATE_PLAN_ID),
                    "check_in": "2026-08-01",
                    "check_out": "2026-08-03",
                    "source": "manual",
                    "adults": 2,
                    "children": 0,
                    "guest": {
                        "first_name": "Dave",
                        "last_name": "Green",
                        "email": "dave@example.com",
                    },
                },
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "confirmed"
        assert body["confirmation_number"].startswith("RES-")

    async def test_cancel_route(self, client, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="confirmed")
        await db.commit()

        with patch("app.services.reservation_service.ari_client") as mock_ari:
            mock_ari.adjust_inventory = AsyncMock(return_value=True)
            resp = await client.post(
                f"/api/v1/reservations/{res.id}/cancel",
                json={"cancellation_reason": "No longer needed"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_status_update_route(self, client, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id, status="confirmed")
        await db.commit()

        resp = await client.post(
            f"/api/v1/reservations/{res.id}/status",
            json={"status": "checked_in"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "checked_in"

    async def test_add_note_route(self, client, db: AsyncSession):
        guest = await make_guest(db)
        res = await make_reservation(db, guest.id)
        await db.commit()

        resp = await client.post(
            f"/api/v1/reservations/{res.id}/notes",
            json={"content": "Late arrival expected."},
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Late arrival expected."

    async def test_duplicates_route(self, client):
        resp = await client.get("/api/v1/reservations/duplicates/scan")
        assert resp.status_code == 200
        data = resp.json()
        assert "groups" in data
        assert "total_duplicates" in data
