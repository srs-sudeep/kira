"""Notification business logic: list, mark read, preferences."""
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ForbiddenError, NotFoundError
from app.repositories.notification_repo import NotificationRepository
from app.repositories.preference_repo import ALL_EVENT_TYPES, PreferenceRepository
from app.schemas.notification import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.schemas.preference import (
    PreferenceResponse,
    PreferencesListResponse,
    PreferencesUpdateRequest,
)

logger = structlog.get_logger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._notif_repo = NotificationRepository(session)
        self._pref_repo = PreferenceRepository(session)

    # ── Notifications ─────────────────────────────────────────────────────────

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        *,
        type_filter: list[str] | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> NotificationListResponse:
        return await self._notif_repo.paginate(
            user_id,
            type_filter=type_filter,
            is_read=is_read,
            page=page,
            page_size=page_size,
        )

    async def get_unread_count(self, user_id: uuid.UUID) -> UnreadCountResponse:
        count = await self._notif_repo.count_unread(user_id)
        return UnreadCountResponse(unread=count)

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> NotificationResponse:
        notif = await self._notif_repo.get_by_id(notification_id)
        if notif is None:
            raise NotFoundError("Notification", str(notification_id))
        if notif.user_id != user_id:
            raise ForbiddenError("You do not own this notification.")
        if notif.is_read:
            return NotificationResponse.model_validate(notif)
        notif = await self._notif_repo.mark_read(notif)
        return NotificationResponse.model_validate(notif)

    async def mark_all_read(self, user_id: uuid.UUID) -> MarkAllReadResponse:
        marked = await self._notif_repo.mark_all_read(user_id)
        logger.info("mark_all_read", user_id=str(user_id), marked=marked)
        return MarkAllReadResponse(marked=marked)

    # ── Preferences ──────────────────────────────────────────────────────────

    async def get_preferences(self, user_id: uuid.UUID) -> PreferencesListResponse:
        """Return the user's saved preferences, filling gaps with defaults."""
        saved = await self._pref_repo.list_for_user(user_id)
        saved_map = {p.event_type: p for p in saved}

        # Build a full list covering all known event types
        items = []
        for event_type in ALL_EVENT_TYPES:
            if event_type in saved_map:
                items.append(PreferenceResponse.model_validate(saved_map[event_type]))
            else:
                # Return a synthetic default — not persisted until PATCH is called
                items.append(
                    PreferenceResponse(
                        id=uuid.uuid4(),  # ephemeral ID for response only
                        user_id=user_id,
                        event_type=event_type,
                        email_enabled=True,
                        in_app_enabled=True,
                        updated_at=__import__("datetime").datetime.now(
                            __import__("datetime").timezone.utc
                        ),
                    )
                )
        return PreferencesListResponse(user_id=user_id, items=items)

    async def update_preferences(
        self,
        user_id: uuid.UUID,
        req: PreferencesUpdateRequest,
    ) -> PreferencesListResponse:
        """Upsert preferences for the given user."""
        prefs_data = [p.model_dump() for p in req.preferences]
        await self._pref_repo.upsert_bulk(user_id, prefs_data)
        logger.info(
            "preferences_updated",
            user_id=str(user_id),
            count=len(req.preferences),
        )
        return await self.get_preferences(user_id)

    # ── Internal: create notifications (called by Kafka consumer) ────────────

    async def create_for_recipients(
        self,
        recipient_ids: list[uuid.UUID],
        *,
        type: str,
        title: str,
        message: str,
        data: dict[str, Any],
    ) -> int:
        """Create in-app notifications for each recipient whose preferences allow it."""
        eligible = []
        for user_id in recipient_ids:
            if await self._pref_repo.is_enabled(user_id, type, "in_app"):
                eligible.append(user_id)

        if not eligible:
            return 0

        count = await self._notif_repo.create_bulk(
            eligible,
            type=type,
            title=title,
            message=message,
            data=data,
        )
        logger.info(
            "notifications_created",
            type=type,
            recipients=len(eligible),
        )
        return count
