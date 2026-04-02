"""pytest fixtures for admin-service tests."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all ORM models on Base.metadata
from app.core import tenant as tenant_module
from app.database import Base, get_db
from app.main import app
from app.models.tenant import Tenant

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_admin_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

FAKE_SUPER_ADMIN_ID = uuid.uuid4()
FAKE_TENANT_ID = uuid.uuid4()
FAKE_TOKEN = "fake-bearer-token"


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db(setup_db):
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def mock_provision_schema():
    """Prevent actual CREATE SCHEMA during tests."""
    with patch(
        "app.repositories.tenant_repo.TenantRepository.provision_schema",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
async def client(db: AsyncSession, mock_provision_schema):
    async def override_get_db():
        yield db

    async def override_get_current_user_id():
        return FAKE_SUPER_ADMIN_ID

    async def override_get_current_user_role():
        return "super_admin"

    async def override_get_tenant_id():
        return FAKE_TENANT_ID

    async def override_raw_token():
        return FAKE_TOKEN

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[tenant_module.get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[tenant_module.get_current_user_role] = override_get_current_user_role
    app.dependency_overrides[tenant_module.get_tenant_id_from_token] = override_get_tenant_id
    app.dependency_overrides[tenant_module.oauth2_scheme] = override_raw_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── ORM factory ───────────────────────────────────────────────────────────────

async def make_tenant(
    session: AsyncSession,
    *,
    name: str = "Test Hotel",
    subscription_tier: str = "starter",
    is_active: bool = True,
    schema_name: str | None = None,
) -> Tenant:
    tenant = Tenant(
        name=name,
        schema_name=schema_name or f"tenant_{uuid.uuid4().hex[:8]}",
        subscription_tier=subscription_tier,
        is_active=is_active,
        country="IND",
        base_currency="INR",
        timezone="Asia/Kolkata",
    )
    session.add(tenant)
    await session.flush()
    await session.refresh(tenant)
    return tenant
