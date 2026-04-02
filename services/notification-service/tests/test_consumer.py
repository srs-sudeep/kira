"""Tests for the Kafka consumer handlers: preference gating, in-app creation, email dispatch."""
import uuid
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_repo import NotificationRepository
from app.repositories.preference_repo import PreferenceRepository
from app.services.notification_service import NotificationService
from tests.conftest import FAKE_TENANT_ID, FAKE_USER_ID, make_preference


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_reservation_created_payload(tenant_id=None):
    return {
        "event": "reservation.created",
        "tenant_id": str(tenant_id or FAKE_TENANT_ID),
        "reservation_id": str(uuid.uuid4()),
        "confirmation_number": "RES-ABC123",
        "source": "manual",
        "room_type_id": str(uuid.uuid4()),
        "rate_plan_id": str(uuid.uuid4()),
        "check_in": "2026-08-01",
        "check_out": "2026-08-03",
        "total_amount": "10000.00",
        "currency": "INR",
        "guest_id": str(uuid.uuid4()),
        "guest_name": "Alice Smith",
    }


def _make_reservation_cancelled_payload(tenant_id=None):
    return {
        "event": "reservation.cancelled",
        "tenant_id": str(tenant_id or FAKE_TENANT_ID),
        "reservation_id": str(uuid.uuid4()),
        "confirmation_number": "RES-XYZ456",
        "cancellation_reason": "Guest request",
        "room_type_id": str(uuid.uuid4()),
        "rate_plan_id": str(uuid.uuid4()),
        "check_in": "2026-08-01",
        "check_out": "2026-08-03",
        "guest_name": "Bob Jones",
    }


def _make_channel_sync_failed_payload(tenant_id=None):
    return {
        "event": "channel.sync.failed",
        "tenant_id": str(tenant_id or FAKE_TENANT_ID),
        "channel_id": str(uuid.uuid4()),
        "channel_name": "Booking.com",
        "ota_code": "booking_com",
        "error_message": "Connection timed out",
    }


# ── create_for_recipients — service layer ────────────────────────────────────

class TestCreateForRecipients:
    async def test_creates_notifications_for_eligible_recipients(self, db: AsyncSession):
        # No saved preferences → defaults to in_app_enabled=True for all
        svc = NotificationService(db)
        count = await svc.create_for_recipients(
            [FAKE_USER_ID],
            type="new_booking",
            title="New Booking",
            message="Reservation confirmed.",
            data={"confirmation_number": "RES-001"},
        )
        assert count == 1

        repo = NotificationRepository(db)
        page = await repo.paginate(FAKE_USER_ID)
        assert page.total == 1
        assert page.items[0].type == "new_booking"

    async def test_skips_recipient_when_in_app_disabled(self, db: AsyncSession):
        await make_preference(
            db, event_type="new_booking", in_app_enabled=False
        )
        await db.commit()

        svc = NotificationService(db)
        count = await svc.create_for_recipients(
            [FAKE_USER_ID],
            type="new_booking",
            title="New Booking",
            message="Reservation confirmed.",
            data={},
        )
        assert count == 0

        repo = NotificationRepository(db)
        page = await repo.paginate(FAKE_USER_ID)
        assert page.total == 0

    async def test_creates_for_multiple_recipients(self, db: AsyncSession):
        from tests.conftest import OTHER_USER_ID

        svc = NotificationService(db)
        count = await svc.create_for_recipients(
            [FAKE_USER_ID, OTHER_USER_ID],
            type="cancellation",
            title="Cancellation",
            message="Reservation cancelled.",
            data={"confirmation_number": "RES-002"},
        )
        assert count == 2

    async def test_returns_zero_when_no_recipients(self, db: AsyncSession):
        svc = NotificationService(db)
        count = await svc.create_for_recipients(
            [],
            type="system",
            title="System",
            message="No one to notify.",
            data={},
        )
        assert count == 0

    async def test_mixed_preferences_partial_creation(self, db: AsyncSession):
        from tests.conftest import OTHER_USER_ID

        # FAKE_USER_ID has in_app disabled, OTHER_USER_ID gets default (enabled)
        await make_preference(
            db, FAKE_USER_ID, event_type="channel_failure", in_app_enabled=False
        )
        await db.commit()

        svc = NotificationService(db)
        count = await svc.create_for_recipients(
            [FAKE_USER_ID, OTHER_USER_ID],
            type="channel_failure",
            title="Channel Failure",
            message="Sync error.",
            data={},
        )
        assert count == 1


# ── Consumer handler functions (unit tests with mocked DB) ───────────────────

class TestConsumerHandlers:
    async def test_handle_reservation_created_dispatches_notifications(
        self, db: AsyncSession
    ):
        """The handler creates in-app notifications for found users."""
        from app.events.consumer import _handle_reservation_created

        recipient_id = uuid.uuid4()
        payload = _make_reservation_created_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch(
                "app.events.consumer._get_recipients",
                AsyncMock(
                    return_value=[
                        {
                            "id": recipient_id,
                            "first_name": "Staff",
                            "last_name": "Member",
                            "email": "staff@hotel.com",
                        }
                    ]
                ),
            ),
            patch("app.events.consumer._dispatch_email_task"),
        ):
            await _handle_reservation_created(db, payload)
            await db.commit()

        repo = NotificationRepository(db)
        page = await repo.paginate(recipient_id)
        assert page.total == 1
        assert page.items[0].type == "new_booking"
        assert "RES-ABC123" in page.items[0].title

    async def test_handle_reservation_cancelled_dispatches_notifications(
        self, db: AsyncSession
    ):
        from app.events.consumer import _handle_reservation_cancelled

        recipient_id = uuid.uuid4()
        payload = _make_reservation_cancelled_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch(
                "app.events.consumer._get_recipients",
                AsyncMock(
                    return_value=[
                        {
                            "id": recipient_id,
                            "first_name": "Front",
                            "last_name": "Desk",
                            "email": "fd@hotel.com",
                        }
                    ]
                ),
            ),
            patch("app.events.consumer._dispatch_email_task"),
        ):
            await _handle_reservation_cancelled(db, payload)
            await db.commit()

        repo = NotificationRepository(db)
        page = await repo.paginate(recipient_id)
        assert page.total == 1
        assert page.items[0].type == "cancellation"

    async def test_handle_channel_sync_failed_dispatches_notifications(
        self, db: AsyncSession
    ):
        from app.events.consumer import _handle_channel_sync_failed

        recipient_id = uuid.uuid4()
        payload = _make_channel_sync_failed_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch(
                "app.events.consumer._get_recipients",
                AsyncMock(
                    return_value=[
                        {
                            "id": recipient_id,
                            "first_name": "Owner",
                            "last_name": "Revenue",
                            "email": "owner@hotel.com",
                        }
                    ]
                ),
            ),
            patch("app.events.consumer._dispatch_email_task"),
        ):
            await _handle_channel_sync_failed(db, payload)
            await db.commit()

        repo = NotificationRepository(db)
        page = await repo.paginate(recipient_id)
        assert page.total == 1
        assert page.items[0].type == "channel_failure"

    async def test_no_notifications_when_no_recipients(self, db: AsyncSession):
        from app.events.consumer import _handle_reservation_created

        payload = _make_reservation_created_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch("app.events.consumer._get_recipients", AsyncMock(return_value=[])),
        ):
            await _handle_reservation_created(db, payload)

        # No notifications created
        repo = NotificationRepository(db)
        page = await repo.paginate(FAKE_USER_ID)
        assert page.total == 0

    async def test_in_app_skipped_when_preference_disabled(self, db: AsyncSession):
        from app.events.consumer import _handle_reservation_created

        recipient_id = FAKE_USER_ID
        # Disable in-app for this event type
        await make_preference(
            db, recipient_id, event_type="new_booking", in_app_enabled=False, email_enabled=True
        )
        await db.commit()

        payload = _make_reservation_created_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch(
                "app.events.consumer._get_recipients",
                AsyncMock(
                    return_value=[
                        {
                            "id": recipient_id,
                            "first_name": "Staff",
                            "last_name": "Member",
                            "email": "staff@hotel.com",
                        }
                    ]
                ),
            ),
            patch("app.events.consumer._dispatch_email_task") as mock_email,
        ):
            await _handle_reservation_created(db, payload)
            await db.commit()

        # No in-app notification
        repo = NotificationRepository(db)
        page = await repo.paginate(recipient_id)
        assert page.total == 0

        # Email task should still be dispatched (email_enabled=True)
        mock_email.assert_called_once()

    async def test_email_skipped_when_preference_disabled(self, db: AsyncSession):
        from app.events.consumer import _handle_reservation_created

        recipient_id = FAKE_USER_ID
        await make_preference(
            db, recipient_id, event_type="new_booking", in_app_enabled=True, email_enabled=False
        )
        await db.commit()

        payload = _make_reservation_created_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch(
                "app.events.consumer._get_recipients",
                AsyncMock(
                    return_value=[
                        {
                            "id": recipient_id,
                            "first_name": "Staff",
                            "last_name": "Member",
                            "email": "staff@hotel.com",
                        }
                    ]
                ),
            ),
            patch("app.events.consumer._dispatch_email_task") as mock_email,
        ):
            await _handle_reservation_created(db, payload)
            await db.commit()

        # In-app notification should exist
        repo = NotificationRepository(db)
        page = await repo.paginate(recipient_id)
        assert page.total == 1

        # No email dispatched
        mock_email.assert_not_called()

    async def test_email_not_dispatched_when_no_email_address(self, db: AsyncSession):
        from app.events.consumer import _handle_reservation_created

        recipient_id = uuid.uuid4()
        payload = _make_reservation_created_payload()

        with (
            patch("app.events.consumer._resolve_schema", AsyncMock(return_value="public")),
            patch(
                "app.events.consumer._get_recipients",
                AsyncMock(
                    return_value=[
                        {
                            "id": recipient_id,
                            "first_name": "No",
                            "last_name": "Email",
                            "email": None,  # no email address
                        }
                    ]
                ),
            ),
            patch("app.events.consumer._dispatch_email_task") as mock_email,
        ):
            await _handle_reservation_created(db, payload)
            await db.commit()

        # In-app created (preference defaults to enabled)
        repo = NotificationRepository(db)
        page = await repo.paginate(recipient_id)
        assert page.total == 1

        # No email (no address)
        mock_email.assert_not_called()


# ── _dispatch_email_task routing ─────────────────────────────────────────────

class TestDispatchEmailTaskRouting:
    def test_routes_new_booking_to_correct_task(self, mock_email_tasks):
        from app.events.consumer import _dispatch_email_task

        kwargs = {
            "to_email": "e@h.com",
            "recipient_name": "Staff",
            "confirmation_number": "RES-001",
            "guest_name": "Guest",
            "check_in": "2026-08-01",
            "check_out": "2026-08-03",
            "room_type": "Deluxe",
            "total_amount": "5000",
            "currency": "INR",
        }
        _dispatch_email_task("new_booking", kwargs)
        mock_email_tasks["new_booking"].delay.assert_called_once_with(**kwargs)

    def test_routes_cancellation_to_correct_task(self, mock_email_tasks):
        from app.events.consumer import _dispatch_email_task

        kwargs = {
            "to_email": "e@h.com",
            "recipient_name": "Staff",
            "confirmation_number": "RES-001",
            "guest_name": "Guest",
            "cancellation_reason": "Reason",
        }
        _dispatch_email_task("cancellation", kwargs)
        mock_email_tasks["cancellation"].delay.assert_called_once_with(**kwargs)

    def test_routes_channel_failure_to_correct_task(self, mock_email_tasks):
        from app.events.consumer import _dispatch_email_task

        kwargs = {
            "to_email": "e@h.com",
            "recipient_name": "Owner",
            "channel_name": "Booking.com",
            "ota_code": "booking_com",
            "error_message": "Timeout",
        }
        _dispatch_email_task("channel_failure", kwargs)
        mock_email_tasks["channel_failure"].delay.assert_called_once_with(**kwargs)

    def test_unknown_event_type_is_no_op(self, mock_email_tasks):
        from app.events.consumer import _dispatch_email_task

        _dispatch_email_task("unknown_type", {})
        mock_email_tasks["new_booking"].delay.assert_not_called()
        mock_email_tasks["cancellation"].delay.assert_not_called()
