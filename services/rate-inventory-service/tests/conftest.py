"""pytest fixtures for rate-inventory-service tests."""
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all models on Base.metadata
from app.database import Base, get_db
from app.main import app
from app.models.rate_plan import RatePlan
from app.models.room_type import RoomType

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_rate_inventory_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

# Fake tenant context injected via JWT mock
FAKE_TENANT_ID = uuid.uuid4()
FAKE_USER_ID = uuid.uuid4()
FAKE_SCHEMA = "tenant_test"


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


# ── Mock kafka and tenant resolution for all tests ────────────────────────────

@pytest.fixture(autouse=True)
def mock_kafka():
    with patch("app.events.producer.kafka_producer") as mock:
        mock.publish_ari_updated = AsyncMock()
        yield mock


@pytest.fixture
async def client(db: AsyncSession):
    """HTTP test client with get_db and tenant middleware overridden."""

    async def override_get_db():
        yield db

    # Override get_tenant_db to skip JWT decode and search_path setting
    from app.core import tenant as tenant_module

    async def override_get_tenant_db():
        yield db

    async def override_get_current_user_id():
        return FAKE_USER_ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[tenant_module.get_tenant_db] = override_get_tenant_db
    app.dependency_overrides[tenant_module.get_current_user_id] = override_get_current_user_id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── ORM factories ─────────────────────────────────────────────────────────────

async def make_room_type(
    session: AsyncSession,
    *,
    name: str = "Deluxe Room",
    max_occupancy: int = 2,
    physical_inventory: int = 10,
    is_active: bool = True,
) -> RoomType:
    rt = RoomType(
        name=name,
        max_occupancy=max_occupancy,
        default_occupancy=2,
        physical_inventory=physical_inventory,
        is_active=is_active,
        amenities=[],
        images=[],
    )
    session.add(rt)
    await session.flush()
    await session.refresh(rt)
    return rt


async def make_rate_plan(
    session: AsyncSession,
    room_type_id: uuid.UUID,
    *,
    name: str = "BAR",
    plan_type: str = "bar",
    base_amount: Decimal = Decimal("5000.00"),
    is_active: bool = True,
    derived_from_id: uuid.UUID | None = None,
    derived_type: str | None = None,
    derived_value: Decimal | None = None,
) -> RatePlan:
    rp = RatePlan(
        room_type_id=room_type_id,
        name=name,
        plan_type=plan_type,
        base_amount=base_amount,
        currency="INR",
        min_los=1,
        max_los=365,
        is_active=is_active,
        derived_from_id=derived_from_id,
        derived_type=derived_type,
        derived_value=derived_value,
    )
    session.add(rp)
    await session.flush()
    await session.refresh(rp)
    return rp
