"""Abstract base adapter — all OTA adapters implement this interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class ARIUpdate:
    """Single date/room-type/rate-plan ARI cell to push to an OTA."""

    ota_room_type_id: str
    ota_rate_plan_id: str
    date: date
    available_rooms: int
    rate_amount: Decimal
    is_closed: bool = False
    min_los: int = 1
    max_los: int = 365


@dataclass
class BookingData:
    """Normalised booking record pulled from an OTA."""

    channel_reservation_id: str
    ota_room_type_id: str
    ota_rate_plan_id: str
    check_in: date
    check_out: date
    total_amount: Decimal
    currency: str
    adults: int
    children: int
    guest_first_name: str
    guest_last_name: str
    guest_email: str | None = None
    guest_phone: str | None = None
    guest_nationality: str | None = None
    special_requests: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Outcome of a single push_ari or pull_bookings call."""

    success: bool
    pushed_count: int = 0
    pulled_count: int = 0
    error_message: str | None = None
    response_status: int | None = None
    response_summary: dict[str, Any] = field(default_factory=dict)


class ChannelAdapter(ABC):
    """Base class for all OTA adapters.

    Each OTA adapter is instantiated with decrypted credentials from the Channel
    record plus an optional config dict.  All methods are async.
    """

    def __init__(self, credentials: dict[str, Any], config: dict[str, Any] | None = None) -> None:
        self.credentials = credentials
        self.config = config or {}

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify that credentials are valid and the OTA API is reachable."""
        ...

    @abstractmethod
    async def push_ari(self, updates: list[ARIUpdate]) -> SyncResult:
        """Push ARI data to the OTA.  Returns a SyncResult summarising the outcome."""
        ...

    @abstractmethod
    async def pull_bookings(self, since: datetime) -> tuple[list[BookingData], SyncResult]:
        """Pull new/modified bookings since the given timestamp.

        Returns a (bookings, result) tuple.  result.success is False if the API
        call itself failed; an empty bookings list with success=True means no new bookings.
        """
        ...
