"""Tests for channel adapters: base interface, registry, and stub implementations."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.adapters.base import ARIUpdate, ChannelAdapter, SyncResult
from app.adapters.booking_com import BookingComAdapter
from app.adapters.expedia import ExpediaAdapter
from app.adapters.makemytrip import MakeMyTripAdapter
from app.adapters.registry import get_adapter, supported_ota_codes
from app.exceptions import ValidationError

TODAY = date.today()
NOW = datetime.now()

_VALID_CREDS: dict[str, dict] = {
    "booking_com": {"api_key": "key123", "hotel_id": "HTL001"},
    "expedia": {"client_id": "cid", "api_secret": "sec", "hotel_id": "EXP001"},
    "makemytrip": {"access_key": "ak", "secret_key": "sk", "property_id": "MMT001"},
}


class TestAdapterRegistry:
    def test_get_adapter_booking_com(self):
        adapter = get_adapter("booking_com", _VALID_CREDS["booking_com"])
        assert isinstance(adapter, BookingComAdapter)

    def test_get_adapter_expedia(self):
        adapter = get_adapter("expedia", _VALID_CREDS["expedia"])
        assert isinstance(adapter, ExpediaAdapter)

    def test_get_adapter_makemytrip(self):
        adapter = get_adapter("makemytrip", _VALID_CREDS["makemytrip"])
        assert isinstance(adapter, MakeMyTripAdapter)

    def test_get_adapter_unknown_raises(self):
        with pytest.raises(ValidationError, match="No adapter registered"):
            get_adapter("unknown_ota", {})

    def test_supported_ota_codes(self):
        codes = supported_ota_codes()
        assert "booking_com" in codes
        assert "expedia" in codes
        assert "makemytrip" in codes

    def test_adapter_receives_config(self):
        config = {"timeout": 30, "retry": True}
        adapter = get_adapter("booking_com", _VALID_CREDS["booking_com"], config=config)
        assert adapter.config == config


class TestAdapterInterface:
    """Verify that all adapters satisfy the ChannelAdapter interface."""

    @pytest.mark.parametrize("ota_code", ["booking_com", "expedia", "makemytrip"])
    def test_all_adapters_are_channel_adapters(self, ota_code):
        adapter = get_adapter(ota_code, _VALID_CREDS[ota_code])
        assert isinstance(adapter, ChannelAdapter)

    @pytest.mark.parametrize("ota_code", ["booking_com", "expedia", "makemytrip"])
    async def test_test_connection_with_valid_creds(self, ota_code):
        adapter = get_adapter(ota_code, _VALID_CREDS[ota_code])
        result = await adapter.test_connection()
        assert result is True

    @pytest.mark.parametrize("ota_code", ["booking_com", "expedia", "makemytrip"])
    async def test_test_connection_with_empty_creds(self, ota_code):
        adapter = get_adapter(ota_code, {})
        result = await adapter.test_connection()
        assert result is False

    @pytest.mark.parametrize("ota_code", ["booking_com", "expedia", "makemytrip"])
    async def test_push_ari_empty_list_returns_zero(self, ota_code):
        adapter = get_adapter(ota_code, _VALID_CREDS[ota_code])
        result = await adapter.push_ari([])
        assert result.success is True
        assert result.pushed_count == 0

    @pytest.mark.parametrize("ota_code", ["booking_com", "expedia", "makemytrip"])
    async def test_push_ari_with_updates(self, ota_code):
        adapter = get_adapter(ota_code, _VALID_CREDS[ota_code])
        updates = [
            ARIUpdate(
                ota_room_type_id="RT_STD",
                ota_rate_plan_id="RP_BAR",
                date=TODAY,
                available_rooms=5,
                rate_amount=Decimal("5000.00"),
            ),
            ARIUpdate(
                ota_room_type_id="RT_STD",
                ota_rate_plan_id="RP_BAR",
                date=TODAY,
                available_rooms=3,
                rate_amount=Decimal("5500.00"),
                is_closed=False,
            ),
        ]
        result = await adapter.push_ari(updates)
        assert isinstance(result, SyncResult)
        assert result.success is True
        assert result.pushed_count == 2
        assert result.response_status == 200

    @pytest.mark.parametrize("ota_code", ["booking_com", "expedia", "makemytrip"])
    async def test_pull_bookings_returns_empty_for_stub(self, ota_code):
        adapter = get_adapter(ota_code, _VALID_CREDS[ota_code])
        bookings, result = await adapter.pull_bookings(since=NOW)
        assert isinstance(bookings, list)
        assert isinstance(result, SyncResult)
        assert result.success is True
        assert result.response_status == 200


class TestARIUpdateDataclass:
    def test_ari_update_defaults(self):
        update = ARIUpdate(
            ota_room_type_id="RT1",
            ota_rate_plan_id="RP1",
            date=TODAY,
            available_rooms=5,
            rate_amount=Decimal("3000"),
        )
        assert update.is_closed is False
        assert update.min_los == 1
        assert update.max_los == 365

    def test_ari_update_override_defaults(self):
        update = ARIUpdate(
            ota_room_type_id="RT1",
            ota_rate_plan_id="RP1",
            date=TODAY,
            available_rooms=0,
            rate_amount=Decimal("4000"),
            is_closed=True,
            min_los=2,
            max_los=14,
        )
        assert update.is_closed is True
        assert update.min_los == 2
        assert update.max_los == 14


class TestSyncResultDataclass:
    def test_success_result(self):
        r = SyncResult(success=True, pushed_count=10, response_status=200)
        assert r.success is True
        assert r.error_message is None

    def test_failure_result(self):
        r = SyncResult(
            success=False,
            error_message="Timeout",
            response_status=504,
        )
        assert r.success is False
        assert r.pushed_count == 0
