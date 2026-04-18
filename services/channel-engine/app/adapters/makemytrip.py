"""MakeMyTrip adapter — stub implementation with mock responses.

Real implementation would use the MakeMyTrip Partner API.
Credentials expected: {"access_key": "...", "secret_key": "...", "property_id": "..."}
"""

from datetime import datetime

import structlog

from app.adapters.base import ARIUpdate, BookingData, ChannelAdapter, SyncResult

logger = structlog.get_logger(__name__)


class MakeMyTripAdapter(ChannelAdapter):
    """Stub MakeMyTrip adapter.

    Replace method bodies with actual MMT Partner API calls in production.
    """

    def _property_id(self) -> str:
        return self.credentials.get("property_id", "MOCK_MMT_PROPERTY")

    async def test_connection(self) -> bool:
        """Test credentials against MakeMyTrip API."""
        access_key = self.credentials.get("access_key")
        secret_key = self.credentials.get("secret_key")
        property_id = self._property_id()
        if not access_key or not secret_key or not property_id:
            logger.warning("mmt_test_connection_missing_credentials")
            return False
        # STUB: always succeed
        logger.info("mmt_test_connection_ok", property_id=property_id)
        return True

    async def push_ari(self, updates: list[ARIUpdate]) -> SyncResult:
        """Push ARI updates to MakeMyTrip.

        Real implementation: POST to MMT Partner API /inventory/update
        """
        if not updates:
            return SyncResult(success=True, pushed_count=0)
        logger.info(
            "mmt_push_ari_stub",
            property_id=self._property_id(),
            cells=len(updates),
        )
        # STUB: simulate success
        return SyncResult(
            success=True,
            pushed_count=len(updates),
            response_status=200,
            response_summary={"status": "SUCCESS", "updated": len(updates)},
        )

    async def pull_bookings(self, since: datetime) -> tuple[list[BookingData], SyncResult]:
        """Pull new bookings from MakeMyTrip.

        Real implementation: GET /bookings?from=<since>&property_id=<id>
        """
        logger.info(
            "mmt_pull_bookings_stub",
            property_id=self._property_id(),
            since=since.isoformat(),
        )
        # STUB: return zero bookings
        return [], SyncResult(success=True, pulled_count=0, response_status=200)
