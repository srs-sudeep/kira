"""Read-only dashboard aggregations (tenant schema)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Display labels for reservation.source
_SOURCE_LABELS: dict[str, str] = {
    "booking_com": "Booking.com",
    "expedia": "Expedia",
    "makemytrip": "MakeMyTrip",
    "airbnb": "Airbnb",
    "agoda": "Agoda",
    "direct": "Direct",
    "manual": "Manual",
    "phone": "Phone",
}


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(100.0 * (current - previous) / previous, 2)


def _map_channel_status(db_status: str) -> str:
    return {
        "connected": "synced",
        "error": "failed",
        "pending_certification": "pending",
        "disconnected": "partial",
    }.get(db_status, "pending")


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def _total_room_inventory(self) -> int:
        row = (
            await self._s.execute(
                text(
                    "SELECT COALESCE(SUM(physical_inventory), 0)::int AS t "
                    "FROM room_types WHERE is_active = true"
                )
            )
        ).mappings().first()
        return int(row["t"] if row else 0)

    async def _room_nights_in_range(self, start: date, end: date) -> tuple[int, float, int, int]:
        """Sum overlapping room-nights, revenue (excl. cancelled), res count, cancelled count."""
        row = (
            await self._s.execute(
                text(
                    """
                    SELECT
                      COALESCE(SUM(
                        CASE WHEN r.status = 'cancelled' THEN 0
                        ELSE GREATEST(
                          0,
                          LEAST(r.check_out, CAST(:end AS date))::int
                          - GREATEST(r.check_in, CAST(:start AS date))::int
                        )
                        END
                      ), 0)::bigint AS room_nights,
                      COALESCE(SUM(CASE WHEN r.status = 'cancelled' THEN 0 ELSE r.total_amount END), 0)::numeric AS revenue,
                      COUNT(*) FILTER (WHERE r.status <> 'cancelled')::int AS res_count,
                      COUNT(*) FILTER (WHERE r.status = 'cancelled')::int AS cancelled
                    FROM reservations r
                    WHERE r.check_in < CAST(:end AS date)
                      AND r.check_out > CAST(:start AS date)
                    """
                ),
                {"start": start, "end": end},
            )
        ).mappings().first()
        if not row:
            return 0, 0.0, 0, 0
        return (
            int(row["room_nights"] or 0),
            float(row["revenue"] or 0),
            int(row["res_count"] or 0),
            int(row["cancelled"] or 0),
        )

    async def kpi_summary(self, days: int) -> dict[str, Any]:
        today = date.today()
        cur_end = today + timedelta(days=1)
        cur_start = today - timedelta(days=days - 1)
        prev_end = cur_start
        prev_start = cur_start - timedelta(days=days)

        inv = await self._total_room_inventory()
        days_in_period = max(1, (cur_end - cur_start).days)

        rn_c, rev_c, cnt_c, can_c = await self._room_nights_in_range(cur_start, cur_end)
        rn_p, rev_p, cnt_p, can_p = await self._room_nights_in_range(prev_start, prev_end)

        cap_nights = max(1, inv * days_in_period)
        occ_c = 100.0 * rn_c / cap_nights
        occ_p = 100.0 * rn_p / cap_nights

        total_c = cnt_c + can_c
        total_p = cnt_p + can_p
        cancel_c = (100.0 * can_c / total_c) if total_c else 0.0
        cancel_p = (100.0 * can_p / total_p) if total_p else 0.0

        return {
            "total_reservations": cnt_c,
            "reservations_change_pct": _pct_change(float(cnt_c), float(cnt_p)),
            "total_revenue": round(rev_c, 2),
            "revenue_change_pct": _pct_change(rev_c, rev_p),
            "occupancy_rate": round(occ_c, 2),
            "occupancy_change_pct": _pct_change(occ_c, occ_p),
            "cancellation_rate": round(cancel_c, 2),
            "cancellation_change_pct": _pct_change(cancel_c, cancel_p),
            "period_label": f"vs previous {days} days",
        }

    async def today_snapshot(self) -> dict[str, Any]:
        today = date.today()
        inv = await self._total_room_inventory()

        row = (
            await self._s.execute(
                text(
                    """
                    SELECT
                      COUNT(*) FILTER (WHERE check_in = :today AND status <> 'cancelled')::int AS arrivals,
                      COUNT(*) FILTER (WHERE check_out = :today AND status <> 'cancelled')::int AS departures,
                      COUNT(*) FILTER (
                        WHERE check_in < :today AND check_out > :today AND status NOT IN ('cancelled', 'no_show')
                      )::int AS stay_overs,
                      COUNT(*) FILTER (WHERE status = 'no_show' AND check_in = :today)::int AS no_shows
                    FROM reservations
                    """
                ),
                {"today": today},
            )
        ).mappings().first()

        occ_row = (
            await self._s.execute(
                text(
                    """
                    SELECT COUNT(*)::int AS n
                    FROM reservations
                    WHERE status NOT IN ('cancelled', 'no_show')
                      AND check_in <= :today AND check_out > :today
                    """
                ),
                {"today": today},
            )
        ).mappings().first()
        occupied = int(occ_row["n"] if occ_row else 0)
        occ_pct = 100.0 * occupied / inv if inv else 0.0

        return {
            "arrivals": int(row["arrivals"] if row else 0),
            "departures": int(row["departures"] if row else 0),
            "stay_overs": int(row["stay_overs"] if row else 0),
            "no_shows": int(row["no_shows"] if row else 0),
            "total_occupied": occupied,
            "total_rooms": inv,
            "occupancy_pct": round(occ_pct, 2),
        }

    async def occupancy_trend(self, days: int) -> list[dict[str, Any]]:
        inv = await self._total_room_inventory()
        end = date.today()
        start = end - timedelta(days=min(days, 90) - 1)

        rows = (
            await self._s.execute(
                text(
                    """
                    WITH days AS (
                      SELECT generate_series(CAST(:start AS date), CAST(:end AS date), '1 day')::date AS d
                    )
                    SELECT
                      d.d AS day,
                      COUNT(r.id) FILTER (
                        WHERE r.status NOT IN ('cancelled', 'no_show')
                          AND r.check_in <= d.d AND r.check_out > d.d
                      )::int AS occupied
                    FROM days d
                    LEFT JOIN reservations r
                      ON r.check_in <= d.d AND r.check_out > d.d
                      AND r.status NOT IN ('cancelled', 'no_show')
                    GROUP BY d.d
                    ORDER BY d.d
                    """
                ),
                {"start": start, "end": end},
            )
        ).mappings().all()

        out: list[dict[str, Any]] = []
        for r in rows:
            occ = int(r["occupied"] or 0)
            avail = max(0, inv - occ)
            pct = 100.0 * occ / inv if inv else 0.0
            out.append(
                {
                    "date": r["day"].isoformat(),
                    "occupancy_pct": round(pct, 2),
                    "occupied_rooms": occ,
                    "available_rooms": avail,
                }
            )
        return out

    async def booking_sources(self, days: int) -> list[dict[str, Any]]:
        today = date.today()
        start = today - timedelta(days=days - 1)
        rows = (
            await self._s.execute(
                text(
                    """
                    SELECT
                      r.source,
                      COUNT(*)::int AS cnt,
                      COALESCE(SUM(CASE WHEN r.status = 'cancelled' THEN 0 ELSE r.total_amount END), 0)::float AS rev
                    FROM reservations r
                    WHERE r.created_at >= CAST(:start AS timestamptz)
                    GROUP BY r.source
                    ORDER BY cnt DESC
                    """
                ),
                {"start": datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)},
            )
        ).mappings().all()

        total = sum(int(r["cnt"]) for r in rows) or 1
        out: list[dict[str, Any]] = []
        for r in rows:
            src = r["source"]
            cnt = int(r["cnt"])
            rev = float(r["rev"] or 0)
            label = _SOURCE_LABELS.get(src, src)
            out.append(
                {
                    "channel": src,
                    "display_name": label,
                    "count": cnt,
                    "percentage": round(100.0 * cnt / total, 2),
                    "revenue": round(rev, 2),
                }
            )
        return out

    async def channel_health(self) -> list[dict[str, Any]]:
        rows = (
            await self._s.execute(
                text(
                    """
                    SELECT c.id, c.ota_code, c.display_name, c.status, c.last_sync_at, c.consecutive_failures,
                           COALESCE((
                             SELECT COUNT(*)::int FROM sync_logs sl
                             WHERE sl.channel_id = c.id
                               AND sl.status = 'failed'
                               AND sl.created_at >= NOW() - interval '24 hours'
                           ), 0) AS err24
                    FROM channels c
                    WHERE c.is_active = true
                    ORDER BY c.display_name
                    """
                )
            )
        ).mappings().all()

        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "channel_id": str(r["id"]),
                    "ota": r["ota_code"],
                    "display_name": r["display_name"],
                    "sync_status": _map_channel_status(r["status"]),
                    "last_synced_at": r["last_sync_at"],
                    "pending_changes": int(r["consecutive_failures"] or 0),
                    "error_count_24h": int(r["err24"] or 0),
                }
            )
        return out
