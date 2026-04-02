"""Repository for notification_preferences."""
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_preference import NotificationPreference

# All known event types — used to generate defaults when none exist
ALL_EVENT_TYPES = (
    "new_booking",
    "cancellation",
    "channel_failure",
    "low_inventory",
    "rate_parity",
    "system",
)


class PreferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, user_id: uuid.UUID, event_type: str) -> NotificationPreference | None:
        return (
            await self._s.execute(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.event_type == event_type,
                )
            )
        ).scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[NotificationPreference]:
        """Return saved preferences, one per event type the user has configured."""
        return list(
            (
                await self._s.execute(
                    select(NotificationPreference)
                    .where(NotificationPreference.user_id == user_id)
                    .order_by(NotificationPreference.event_type)
                )
            )
            .scalars()
            .all()
        )

    async def is_enabled(
        self,
        user_id: uuid.UUID,
        event_type: str,
        channel: str,  # "email" | "in_app"
    ) -> bool:
        """Return True if the given channel is enabled for this user/event.

        Defaults to True when no preference record exists.
        """
        pref = await self.get(user_id, event_type)
        if pref is None:
            return True
        return bool(getattr(pref, f"{channel}_enabled"))

    async def upsert(
        self,
        user_id: uuid.UUID,
        event_type: str,
        email_enabled: bool,
        in_app_enabled: bool,
    ) -> NotificationPreference:
        """Insert or update a single preference row."""
        stmt = (
            pg_insert(NotificationPreference)
            .values(
                user_id=user_id,
                event_type=event_type,
                email_enabled=email_enabled,
                in_app_enabled=in_app_enabled,
            )
            .on_conflict_do_update(
                constraint="uq_pref",
                set_={
                    "email_enabled": email_enabled,
                    "in_app_enabled": in_app_enabled,
                },
            )
            .returning(NotificationPreference)
        )
        result = (await self._s.execute(stmt)).scalar_one()
        return result

    async def upsert_bulk(
        self,
        user_id: uuid.UUID,
        preferences: list[dict[str, Any]],
    ) -> list[NotificationPreference]:
        """Upsert multiple preferences at once."""
        rows = []
        for p in preferences:
            rows.append(
                await self.upsert(
                    user_id,
                    p["event_type"],
                    p["email_enabled"],
                    p["in_app_enabled"],
                )
            )
        return rows
