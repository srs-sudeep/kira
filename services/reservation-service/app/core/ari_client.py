"""HTTP client for calling the rate-inventory-service to check/modify ARI.

Availability check: GET /api/v1/inventory/calendar
Inventory decrement/increment: PUT /api/v1/inventory/calendar
"""
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

import httpx
import structlog

from app.config import settings
from app.exceptions import ValidationError

logger = structlog.get_logger(__name__)


@dataclass
class AvailabilityResult:
    available: bool
    total_amount: Decimal = Decimal("0")
    rates_per_night: dict[str, Decimal] = field(default_factory=dict)
    reason: str | None = None


class ARIClient:
    """Thin async HTTP wrapper around the rate-inventory-service API."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base = (base_url or settings.rate_inventory_service_url).rstrip("/")

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    async def check_availability(
        self,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        check_in: date,
        check_out: date,
        token: str,
        tenant_id: uuid.UUID,
    ) -> AvailabilityResult:
        """
        Return availability and per-night rates for the requested date range.
        Returns AvailabilityResult.available=False if any date is closed or sold out.
        """
        url = f"{self._base}/api/v1/inventory/calendar"
        params = {
            "room_type_id": str(room_type_id),
            "start_date": check_in.isoformat(),
            "end_date": (check_out - timedelta(days=1)).isoformat(),
            "tenant_id": str(tenant_id),
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params, headers=self._headers(token))
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("ari_check_http_error", status=exc.response.status_code)
            return AvailabilityResult(available=False, reason=f"Rate service error: {exc.response.status_code}")
        except httpx.RequestError as exc:
            logger.warning("ari_check_request_error", exc=str(exc))
            return AvailabilityResult(available=False, reason="Rate service unreachable")

        data = resp.json()
        rates: dict[str, Decimal] = {}
        nights = (check_out - check_in).days

        for rt_row in data.get("room_types", []):
            for rp_row in rt_row.get("rate_plans", []):
                if str(rp_row["rate_plan_id"]) != str(rate_plan_id):
                    continue
                for d_str, cell in rp_row.get("cells", {}).items():
                    if cell.get("is_closed") or cell.get("available_rooms", 0) < 1:
                        return AvailabilityResult(
                            available=False,
                            reason=f"Room not available on {d_str}",
                        )
                    rates[d_str] = Decimal(str(cell["rate_amount"]))

        if len(rates) < nights:
            return AvailabilityResult(
                available=False,
                reason="ARI data incomplete for the requested date range",
            )

        total = sum(rates.values())
        return AvailabilityResult(available=True, total_amount=total, rates_per_night=rates)

    async def adjust_inventory(
        self,
        room_type_id: uuid.UUID,
        rate_plan_id: uuid.UUID,
        check_in: date,
        check_out: date,
        delta: int,  # -1 to decrement (book), +1 to increment (cancel)
        token: str,
        tenant_id: uuid.UUID,
    ) -> bool:
        """Adjust available_rooms by delta for each night in the stay."""
        url = f"{self._base}/api/v1/inventory/calendar"
        nights = (check_out - check_in).days
        cells = []
        for i in range(nights):
            d = check_in + timedelta(days=i)
            cells.append({
                "room_type_id": str(room_type_id),
                "rate_plan_id": str(rate_plan_id),
                "date": d.isoformat(),
                "available_rooms": delta,  # will be added by rate service
            })
        params = {"tenant_id": str(tenant_id)}
        body = {"cells": cells}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(
                    url, json=body, params=params, headers=self._headers(token)
                )
                resp.raise_for_status()
            return True
        except Exception as exc:
            logger.error("ari_adjust_failed", delta=delta, exc=str(exc))
            return False


# Module-level singleton — overridden in tests
ari_client = ARIClient()
