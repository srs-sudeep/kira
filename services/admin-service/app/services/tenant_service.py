"""Tenant management service — create, list, update, and provision schemas."""
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.repositories.tenant_repo import TenantRepository
from app.schemas.tenant import (
    TenantAdminUpdate,
    TenantCreate,
    TenantListResponse,
    TenantMeUpdate,
    TenantResponse,
)

logger = structlog.get_logger(__name__)


def _generate_schema_name() -> str:
    """Generate a unique, safe schema name: tenant_{8-char hex}."""
    return f"tenant_{uuid.uuid4().hex[:8]}"


class TenantService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = TenantRepository(session)

    async def create_tenant(self, req: TenantCreate) -> TenantResponse:
        """Create a new tenant record and provision its PostgreSQL schema.

        Steps:
        1. Generate a unique schema_name.
        2. INSERT the tenant record (flush, not commit).
        3. CREATE SCHEMA + create all tenant tables.
        4. The caller (get_db dependency) commits the transaction.
        """
        schema_name = _generate_schema_name()
        # Verify uniqueness — extremely unlikely collision but safe to check
        existing = await self._repo.get_by_schema_name(schema_name)
        if existing:
            schema_name = _generate_schema_name()  # one retry

        tenant = await self._repo.create(
            name=req.name,
            schema_name=schema_name,
            legal_name=req.legal_name,
            address_line1=req.address_line1,
            address_line2=req.address_line2,
            city=req.city,
            state=req.state,
            country=req.country,
            postal_code=req.postal_code,
            phone=req.phone,
            email=req.email,
            website=req.website,
            star_rating=req.star_rating,
            base_currency=req.base_currency,
            timezone=req.timezone,
            logo_url=req.logo_url,
            subscription_tier=req.subscription_tier,
        )

        await self._repo.provision_schema(schema_name)

        logger.info(
            "tenant_created",
            tenant_id=str(tenant.id),
            schema_name=schema_name,
        )
        return TenantResponse.model_validate(tenant)

    async def list_tenants(
        self, *, page: int = 1, page_size: int = 50
    ) -> TenantListResponse:
        return await self._repo.list_all(page=page, page_size=page_size)

    async def get_tenant(self, tenant_id: uuid.UUID) -> TenantResponse:
        tenant = await self._repo.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant", str(tenant_id))
        return TenantResponse.model_validate(tenant)

    async def get_my_tenant(self, tenant_id: uuid.UUID) -> TenantResponse:
        return await self.get_tenant(tenant_id)

    async def update_tenant(
        self, tenant_id: uuid.UUID, req: TenantAdminUpdate
    ) -> TenantResponse:
        """super_admin can update subscription_tier, is_active, and name."""
        tenant = await self._repo.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant", str(tenant_id))

        fields = req.model_dump(exclude_none=True)
        if not fields:
            return TenantResponse.model_validate(tenant)

        updated = await self._repo.update(tenant_id, fields)
        return TenantResponse.model_validate(updated)

    async def update_my_tenant(
        self, tenant_id: uuid.UUID, req: TenantMeUpdate
    ) -> TenantResponse:
        """property_owner can update their own tenant's profile fields."""
        tenant = await self._repo.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant", str(tenant_id))

        fields = req.model_dump(exclude_none=True)
        if not fields:
            return TenantResponse.model_validate(tenant)

        updated = await self._repo.update(tenant_id, fields)
        logger.info("tenant_profile_updated", tenant_id=str(tenant_id))
        return TenantResponse.model_validate(updated)
