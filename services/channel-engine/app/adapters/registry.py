"""Adapter registry — maps ota_code strings to ChannelAdapter subclasses.

Usage:
    adapter = get_adapter(ota_code, credentials, config)
    ok = await adapter.test_connection()
"""
from typing import Any

from app.adapters.base import ChannelAdapter
from app.adapters.booking_com import BookingComAdapter
from app.adapters.expedia import ExpediaAdapter
from app.adapters.makemytrip import MakeMyTripAdapter
from app.exceptions import ValidationError

_REGISTRY: dict[str, type[ChannelAdapter]] = {
    "booking_com": BookingComAdapter,
    "expedia": ExpediaAdapter,
    "makemytrip": MakeMyTripAdapter,
}


def get_adapter(
    ota_code: str,
    credentials: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> ChannelAdapter:
    """Instantiate and return the correct adapter for the given ota_code.

    Raises ValidationError for unknown OTA codes.
    """
    cls = _REGISTRY.get(ota_code)
    if cls is None:
        raise ValidationError(
            f"No adapter registered for OTA '{ota_code}'. "
            f"Supported: {sorted(_REGISTRY.keys())}"
        )
    return cls(credentials=credentials, config=config or {})


def supported_ota_codes() -> list[str]:
    return sorted(_REGISTRY.keys())
