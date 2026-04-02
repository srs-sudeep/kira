"""Repository for public.audit_events — append-only writes, filtered reads."""
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.schemas.audit import AuditFilterParams


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        *,
        action: str,
        tenant_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        event_metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            action=action,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=event_metadata,
        )
        self._s.add(event)
        await self._s.flush()
        return event

    async def list_filtered(
        self, filters: AuditFilterParams
    ) -> tuple[list[AuditEvent], int]:
        base = select(AuditEvent)

        if filters.tenant_id is not None:
            base = base.where(AuditEvent.tenant_id == filters.tenant_id)
        if filters.user_id is not None:
            base = base.where(AuditEvent.user_id == filters.user_id)
        if filters.action is not None:
            base = base.where(AuditEvent.action == filters.action)
        if filters.resource_type is not None:
            base = base.where(AuditEvent.resource_type == filters.resource_type)
        if filters.resource_id is not None:
            base = base.where(AuditEvent.resource_id == filters.resource_id)
        if filters.from_dt is not None:
            base = base.where(AuditEvent.created_at >= filters.from_dt)
        if filters.to_dt is not None:
            base = base.where(AuditEvent.created_at <= filters.to_dt)

        total = (
            await self._s.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._s.execute(
                base.order_by(AuditEvent.created_at.desc())
                .offset((filters.page - 1) * filters.page_size)
                .limit(filters.page_size)
            )
        ).scalars().all()
        return list(rows), total
