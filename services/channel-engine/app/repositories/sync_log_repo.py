"""Repository for sync_logs."""
import math
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_log import SyncLog
from app.schemas.sync_log import SyncLogPageResponse, SyncLogResponse


class SyncLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        *,
        channel_id: uuid.UUID,
        event_type: str,
        direction: str,
        status: str,
        payload_hash: str | None = None,
        request_summary: dict[str, Any] | None = None,
        response_status: int | None = None,
        response_summary: dict[str, Any] | None = None,
        retry_count: int = 0,
    ) -> SyncLog:
        log = SyncLog(
            channel_id=channel_id,
            event_type=event_type,
            direction=direction,
            status=status,
            payload_hash=payload_hash,
            request_summary=request_summary,
            response_status=response_status,
            response_summary=response_summary,
            retry_count=retry_count,
        )
        self._s.add(log)
        await self._s.flush()
        await self._s.refresh(log)
        return log

    async def paginate(
        self,
        channel_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> SyncLogPageResponse:
        base_q = select(SyncLog).where(SyncLog.channel_id == channel_id)
        total: int = (
            await self._s.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._s.execute(
                base_q.order_by(SyncLog.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return SyncLogPageResponse(
            items=[SyncLogResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )
