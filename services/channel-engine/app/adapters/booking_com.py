"""Booking.com adapter — stub implementation with mock responses.

Real implementation would use the Booking.com Connectivity API (XML/JSON over HTTPS).
Credentials expected: {"api_key": "...", "hotel_id": "..."}
"""

from datetime import datetime
from decimal import Decimal

import structlog

from app.adapters.base import ARIUpdate, BookingData, ChannelAdapter, SyncResult

logger = structlog.get_logger(__name__)

_MOCK_BOOKING = BookingData(
    channel_reservation_id="BDC-MOCK-001",
    ota_room_type_id="RT_STANDARD",
    ota_rate_plan_id="RP_BAR",
    check_in=datetime.now().date(),
    check_out=datetime.now().date(),
    total_amount=Decimal("5000.00"),
    currency="INR",
    adults=2,
    children=0,
    guest_first_name="Mock",
    guest_last_name="Guest",
    guest_email="mock@booking.com",
    raw_payload={"source": "booking_com_mock"},
)


class BookingComAdapter(ChannelAdapter):
    """Stub Booking.com adapter.

    All API calls are mocked — no real HTTP requests are made.
    Replace method bodies with actual Booking.com API calls in production.
    """

    def _hotel_id(self) -> str:
        return self.credentials.get("hotel_id", "MOCK_HOTEL")

    async def test_connection(self) -> bool:
        """Validate credentials against the Booking.com API."""
        api_key = self.credentials.get("api_key")
        hotel_id = self._hotel_id()
        if not api_key or not hotel_id:
            logger.warning("booking_com_test_connection_missing_credentials")
            return False
        # STUB: always succeed
        logger.info("booking_com_test_connection_ok", hotel_id=hotel_id)
        return True

    async def push_ari(self, updates: list[ARIUpdate]) -> SyncResult:
        """Push ARI updates to Booking.com.

        Real implementation: POST /1.0/json?auth_token=...&type=ar&hotel_id=...
        """
        if not updates:
            return SyncResult(success=True, pushed_count=0)
        logger.info(
            "booking_com_push_ari_stub",
            hotel_id=self._hotel_id(),
            cells=len(updates),
        )
        # STUB: simulate success
        return SyncResult(
            success=True,
            pushed_count=len(updates),
            response_status=200,
            response_summary={"status": "ok", "cells_updated": len(updates)},
        )

    async def pull_bookings(self, since: datetime) -> tuple[list[BookingData], SyncResult]:
        """Pull new reservations from Booking.com since a given datetime.

        Real implementation: GET /1.0/json?auth_token=...&type=reservations&hotel_id=...
        """
        logger.info(
            "booking_com_pull_bookings_stub",
            hotel_id=self._hotel_id(),
            since=since.isoformat(),
        )
        # STUB: return zero bookings so tests don't get noisy
        return [], SyncResult(success=True, pulled_count=0, response_status=200)
