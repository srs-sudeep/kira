"""Tests for tenant CRUD: create, list, get, update, schema provisioning."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.repositories.tenant_repo import TenantRepository
from app.services.tenant_service import TenantService, _generate_schema_name
from app.schemas.tenant import TenantAdminUpdate, TenantCreate, TenantMeUpdate
from tests.conftest import FAKE_TENANT_ID, make_tenant


# ── Schema name generation ────────────────────────────────────────────────────


class TestSchemaNameGeneration:
    def test_schema_name_format(self):
        name = _generate_schema_name()
        assert name.startswith("tenant_")
        assert len(name) == len("tenant_") + 8

    def test_schema_names_are_unique(self):
        names = {_generate_schema_name() for _ in range(20)}
        assert len(names) == 20

    def test_schema_name_is_safe(self):
        for _ in range(10):
            name = _generate_schema_name()
            assert all(c.isalnum() or c == "_" for c in name)


# ── TenantService — service layer ─────────────────────────────────────────────


class TestCreateTenant:
    async def test_creates_tenant_record(self, db: AsyncSession, mock_provision_schema):
        svc = TenantService(db)
        result = await svc.create_tenant(TenantCreate(name="Grand Hyatt Mumbai", subscription_tier="professional"))
        assert result.name == "Grand Hyatt Mumbai"
        assert result.subscription_tier == "professional"
        assert result.schema_name.startswith("tenant_")
        assert result.is_active is True

    async def test_provisions_schema_on_create(self, db: AsyncSession, mock_provision_schema):
        svc = TenantService(db)
        await svc.create_tenant(TenantCreate(name="Test Hotel"))
        mock_provision_schema.assert_called_once()

    async def test_schema_name_passed_to_provision(self, db: AsyncSession, mock_provision_schema):
        svc = TenantService(db)
        result = await svc.create_tenant(TenantCreate(name="Hotel Leela"))
        called_with = mock_provision_schema.call_args[0][0]
        assert called_with == result.schema_name

    async def test_sets_defaults(self, db: AsyncSession, mock_provision_schema):
        svc = TenantService(db)
        result = await svc.create_tenant(TenantCreate(name="Minimal Hotel"))
        assert result.country == "IND"
        assert result.base_currency == "INR"
        assert result.timezone == "Asia/Kolkata"
        assert result.onboarded_at is not None

    async def test_full_address_stored(self, db: AsyncSession, mock_provision_schema):
        svc = TenantService(db)
        result = await svc.create_tenant(
            TenantCreate(
                name="Taj Mahal Palace",
                address_line1="Apollo Bunder",
                city="Mumbai",
                state="Maharashtra",
                postal_code="400001",
                star_rating=5,
                phone="+91-22-6665-3366",
            )
        )
        assert result.city == "Mumbai"
        assert result.star_rating == 5
        assert result.postal_code == "400001"


class TestListTenants:
    async def test_empty_list(self, db: AsyncSession):
        svc = TenantService(db)
        result = await svc.list_tenants()
        assert result.total == 0
        assert result.items == []

    async def test_returns_all_tenants(self, db: AsyncSession):
        await make_tenant(db, name="Hotel A")
        await make_tenant(db, name="Hotel B")
        await make_tenant(db, name="Hotel C")
        await db.commit()

        svc = TenantService(db)
        result = await svc.list_tenants()
        assert result.total == 3

    async def test_pagination(self, db: AsyncSession):
        for i in range(5):
            await make_tenant(db, name=f"Hotel {i}")
        await db.commit()

        svc = TenantService(db)
        result = await svc.list_tenants(page=2, page_size=2)
        assert result.page == 2
        assert len(result.items) == 2
        assert result.pages == 3
        assert result.total == 5

    async def test_first_page(self, db: AsyncSession):
        for i in range(3):
            await make_tenant(db, name=f"Hotel {i}")
        await db.commit()

        svc = TenantService(db)
        result = await svc.list_tenants(page=1, page_size=2)
        assert len(result.items) == 2


class TestGetTenant:
    async def test_returns_tenant_by_id(self, db: AsyncSession):
        tenant = await make_tenant(db, name="The Oberoi")
        await db.commit()

        svc = TenantService(db)
        result = await svc.get_tenant(tenant.id)
        assert result.id == tenant.id
        assert result.name == "The Oberoi"

    async def test_raises_not_found(self, db: AsyncSession):
        svc = TenantService(db)
        with pytest.raises(NotFoundError):
            await svc.get_tenant(uuid.uuid4())


class TestUpdateTenant:
    async def test_update_subscription_tier(self, db: AsyncSession):
        tenant = await make_tenant(db, subscription_tier="starter")
        await db.commit()

        svc = TenantService(db)
        result = await svc.update_tenant(
            tenant.id,
            TenantAdminUpdate(subscription_tier="enterprise"),
        )
        assert result.subscription_tier == "enterprise"

    async def test_deactivate_tenant(self, db: AsyncSession):
        tenant = await make_tenant(db, is_active=True)
        await db.commit()

        svc = TenantService(db)
        result = await svc.update_tenant(tenant.id, TenantAdminUpdate(is_active=False))
        assert result.is_active is False

    async def test_no_op_when_empty_update(self, db: AsyncSession):
        tenant = await make_tenant(db, name="Unchanged Hotel")
        await db.commit()

        svc = TenantService(db)
        result = await svc.update_tenant(tenant.id, TenantAdminUpdate())
        assert result.name == "Unchanged Hotel"

    async def test_raises_not_found(self, db: AsyncSession):
        svc = TenantService(db)
        with pytest.raises(NotFoundError):
            await svc.update_tenant(uuid.uuid4(), TenantAdminUpdate(is_active=False))


class TestUpdateMyTenant:
    async def test_update_profile_fields(self, db: AsyncSession):
        tenant = await make_tenant(db, name="Old Name")
        await db.commit()

        svc = TenantService(db)
        result = await svc.update_my_tenant(
            tenant.id,
            TenantMeUpdate(name="New Name", city="Delhi", star_rating=4),
        )
        assert result.name == "New Name"
        assert result.city == "Delhi"
        assert result.star_rating == 4

    async def test_no_op_when_empty(self, db: AsyncSession):
        tenant = await make_tenant(db, name="Stable Hotel")
        await db.commit()

        svc = TenantService(db)
        result = await svc.update_my_tenant(tenant.id, TenantMeUpdate())
        assert result.name == "Stable Hotel"


# ── TenantRepository ──────────────────────────────────────────────────────────


class TestTenantRepository:
    async def test_get_by_id_returns_none_for_unknown(self, db: AsyncSession):
        repo = TenantRepository(db)
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_get_by_schema_name(self, db: AsyncSession):
        tenant = await make_tenant(db, schema_name="tenant_abc123de")
        await db.commit()

        repo = TenantRepository(db)
        found = await repo.get_by_schema_name("tenant_abc123de")
        assert found is not None
        assert found.id == tenant.id

    async def test_schema_name_is_unique(self, db: AsyncSession):
        schema = f"tenant_{uuid.uuid4().hex[:8]}"
        await make_tenant(db, schema_name=schema)
        await db.commit()

        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await make_tenant(db, schema_name=schema)
            await db.commit()


# ── HTTP routes ───────────────────────────────────────────────────────────────


class TestTenantRoutes:
    async def test_create_tenant_route(self, client, mock_provision_schema):
        resp = await client.post(
            "/api/v1/tenants",
            json={"name": "Route Test Hotel", "subscription_tier": "starter"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Route Test Hotel"
        assert "schema_name" in data
        assert data["schema_name"].startswith("tenant_")

    async def test_list_tenants_route(self, client, db: AsyncSession):
        await make_tenant(db, name="Hotel Alpha")
        await make_tenant(db, name="Hotel Beta")
        await db.commit()

        resp = await client.get("/api/v1/tenants")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    async def test_get_my_tenant_route(self, client, db: AsyncSession):
        # FAKE_TENANT_ID is the override tenant — create a matching record
        from app.models.tenant import Tenant

        tenant = Tenant(
            id=FAKE_TENANT_ID,
            name="My Hotel",
            schema_name=f"tenant_{uuid.uuid4().hex[:8]}",
            country="IND",
            base_currency="INR",
            timezone="Asia/Kolkata",
            subscription_tier="starter",
            is_active=True,
        )
        db.add(tenant)
        await db.commit()

        resp = await client.get("/api/v1/tenants/me")
        assert resp.status_code == 200
        assert resp.json()["name"] == "My Hotel"

    async def test_update_tenant_route(self, client, db: AsyncSession):
        tenant = await make_tenant(db, subscription_tier="starter")
        await db.commit()

        resp = await client.patch(
            f"/api/v1/tenants/{tenant.id}",
            json={"subscription_tier": "professional"},
        )
        assert resp.status_code == 200
        assert resp.json()["subscription_tier"] == "professional"

    async def test_get_tenant_not_found(self, client):
        resp = await client.get(f"/api/v1/tenants/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_list_pagination_params(self, client, db: AsyncSession):
        for i in range(6):
            await make_tenant(db, name=f"Hotel {i}")
        await db.commit()

        resp = await client.get("/api/v1/tenants?page=2&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert len(data["items"]) == 2
