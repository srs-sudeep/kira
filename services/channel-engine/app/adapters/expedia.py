"""Expedia adapter — stub implementation with mock responses.

Real implementation would use the Expedia Rapid API (EQC) or Expedia Partner Central API.
Credentials expected: {"client_id": "...", "api_secret": "...", "hotel_id": "..."}
"""

from datetime import datetime

import structlog

from app.adapters.base import ARIUpdate, BookingData, ChannelAdapter, SyncResult

logger = structlog.get_logger(__name__)


class ExpediaAdapter(ChannelAdapter):
    """Stub Expedia adapter.

    Replace method bodies with actual Expedia EQC/Rapid API calls in production.
    """

    def _hotel_id(self) -> str:
        return self.credentials.get("hotel_id", "MOCK_EXPEDIA_HOTEL")

    async def test_connection(self) -> bool:
        """Test credentials against Expedia API."""
        client_id = self.credentials.get("client_id")
        api_secret = self.credentials.get("api_secret")
        hotel_id = self._hotel_id()
        if not client_id or not api_secret or not hotel_id:
            logger.warning("expedia_test_connection_missing_credentials")
            return False
        # STUB: always succeed
        logger.info("expedia_test_connection_ok", hotel_id=hotel_id)
        return True

    async def push_ari(self, updates: list[ARIUpdate]) -> SyncResult:
        """Push ARI updates to Expedia EQC.

        Real implementation: EQC AR Message — HTTPS POST to
        https://services.expediapartnercentral.com/eqc/ar
        """
        if not updates:
            return SyncResult(success=True, pushed_count=0)
        logger.info(
            "expedia_push_ari_stub",
            hotel_id=self._hotel_id(),
            cells=len(updates),
        )
        # STUB: simulate success
        return SyncResult(
            success=True,
            pushed_count=len(updates),
            response_status=200,
            response_summary={"status": "success", "cells_updated": len(updates)},
        )

    async def pull_bookings(self, since: datetime) -> tuple[list[BookingData], SyncResult]:
        """Pull new bookings from Expedia since a given datetime.

        Real implementation: EQC BR Message — HTTPS GET to
        https://services.expediapartnercentral.com/eqc/br
        """
        logger.info(
            "expedia_pull_bookings_stub",
            hotel_id=self._hotel_id(),
            since=since.isoformat(),
        )
        # STUB: return zero bookings
        return [], SyncResult(success=True, pulled_count=0, response_status=200)
