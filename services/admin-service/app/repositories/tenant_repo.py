"""Repository for public.tenants — CRUD + raw-schema provisioning."""

import math
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.tenant import TenantListResponse, TenantResponse

logger = structlog.get_logger(__name__)


def _tenant_tables_ddl() -> str:
    """Load shared/tenant_tables.sql from repo root (works in Docker with /app/shared mount)."""
    here = Path(__file__).resolve()
    for anc in here.parents:
        p = anc / "shared" / "tenant_tables.sql"
        if p.is_file():
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError("shared/tenant_tables.sql not found (mount repo shared/ or build image with COPY)")


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        return (await self._s.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()

    async def get_by_schema_name(self, schema_name: str) -> Tenant | None:
        return (await self._s.execute(select(Tenant).where(Tenant.schema_name == schema_name))).scalar_one_or_none()

    async def list_all(self, *, page: int = 1, page_size: int = 50) -> TenantListResponse:
        total: int = (await self._s.execute(select(func.count()).select_from(Tenant))).scalar_one()

        rows = (
            (
                await self._s.execute(
                    select(Tenant).order_by(Tenant.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
                )
            )
            .scalars()
            .all()
        )

        return TenantListResponse(
            items=[TenantResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            pages=max(1, math.ceil(total / page_size)),
        )

    async def create(
        self,
        *,
        name: str,
        schema_name: str,
        legal_name: str | None = None,
        address_line1: str | None = None,
        address_line2: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str = "IND",
        postal_code: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        website: str | None = None,
        star_rating: int | None = None,
        base_currency: str = "INR",
        timezone: str = "Asia/Kolkata",
        logo_url: str | None = None,
        subscription_tier: str = "starter",
    ) -> Tenant:
        tenant = Tenant(
            name=name,
            schema_name=schema_name,
            legal_name=legal_name,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            phone=phone,
            email=email,
            website=website,
            star_rating=star_rating,
            base_currency=base_currency,
            timezone=timezone,
            logo_url=logo_url,
            subscription_tier=subscription_tier,
            onboarded_at=datetime.now(UTC),
        )
        self._s.add(tenant)
        await self._s.flush()
        await self._s.refresh(tenant)
        return tenant

    async def update(self, tenant_id: uuid.UUID, fields: dict[str, Any]) -> Tenant | None:
        await self._s.execute(update(Tenant).where(Tenant.id == tenant_id).values(**fields))
        return await self.get_by_id(tenant_id)

    async def provision_schema(self, schema_name: str) -> None:
        """Create PostgreSQL schema + all tenant business tables.

        Executes DDL within the current transaction. Called immediately after
        the Tenant record is flushed (but before commit) so that a failed
        schema creation rolls back the tenant insert automatically.
        """
        # Validate schema name to prevent SQL injection (alphanumeric + underscore only)
        if not all(c.isalnum() or c == "_" for c in schema_name):
            raise ValueError(f"Invalid schema name: {schema_name!r}")

        await self._s.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        logger.info("schema_created", schema_name=schema_name)

        # Create all per-tenant business tables within the new schema.
        # search_path is set so FK references resolve within the schema.
        await self._s.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
        await self._s.execute(text(_tenant_tables_ddl()))
        logger.info("tenant_tables_created", schema_name=schema_name)
