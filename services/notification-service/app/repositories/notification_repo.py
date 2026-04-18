"""Repository for notifications."""

import math
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return (
            await self._s.execute(select(Notification).where(Notification.id == notification_id))
        ).scalar_one_or_none()

    async def paginate(
        self,
        user_id: uuid.UUID,
        *,
        type_filter: list[str] | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> NotificationListResponse:
        base_q = select(Notification).where(Notification.user_id == user_id)
        if type_filter:
            base_q = base_q.where(Notification.type.in_(type_filter))
        if is_read is not None:
            base_q = base_q.where(Notification.is_read.is_(is_read))

        total: int = (await self._s.execute(select(func.count()).select_from(base_q.subquery()))).scalar_one()

        unread: int = (
            await self._s.execute(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            )
        ).scalar_one()

        rows = (
            (
                await self._s.execute(
                    base_q.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
                )
            )
            .scalars()
            .all()
        )

        return NotificationListResponse(
            items=[NotificationResponse.model_validate(r) for r in rows],
            total=total,
            unread=unread,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )

    async def count_unread(self, user_id: uuid.UUID) -> int:
        return (
            await self._s.execute(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                )
            )
        ).scalar_one()

    async def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await self._s.flush()
        await self._s.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self._s.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        return result.rowcount

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        type: str,
        title: str,
        message: str,
        data: dict,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data,
        )
        self._s.add(notif)
        await self._s.flush()
        await self._s.refresh(notif)
        return notif

    async def create_bulk(
        self,
        recipients: list[uuid.UUID],
        *,
        type: str,
        title: str,
        message: str,
        data: dict,
    ) -> int:
        """Create one notification per recipient. Returns count created."""
        count = 0
        for user_id in recipients:
            notif = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                data=data,
            )
            self._s.add(notif)
            count += 1
        if count:
            await self._s.flush()
        return count
