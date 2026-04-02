"""KIRA datetime utilities — timezone-aware helpers used across services."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(tz=timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert a naive or offset-aware datetime to UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def date_range(start: date, end: date) -> list[date]:
    """Return every date in [start, end] inclusive."""
    if end < start:
        raise ValueError(f"end ({end}) must be >= start ({start})")
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


def nights_between(check_in: date, check_out: date) -> int:
    """Return the number of nights between check-in and check-out."""
    if check_out <= check_in:
        raise ValueError("check_out must be after check_in")
    return (check_out - check_in).days


def parse_iso_date(value: str) -> date:
    """Parse an ISO-8601 date string (YYYY-MM-DD) into a :class:`date`."""
    return date.fromisoformat(value)


def format_iso_date(d: date) -> str:
    """Format a :class:`date` as an ISO-8601 string."""
    return d.isoformat()
