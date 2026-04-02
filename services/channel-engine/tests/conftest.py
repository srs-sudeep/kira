"""pytest fixtures for channel-engine tests."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all ORM models on Base.metadata
from app.database import Base, get_db
from app.main import app
from app.models.channel import Channel
from app.models.channel_mapping import ChannelMapping

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_channel_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

FAKE_TENANT_ID = uuid.uuid4()
FAKE_USER_ID = uuid.uuid4()
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


# ── Kafka mock — applied to all tests ────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_kafka():
    with patch("app.events.producer.kafka_producer") as mock:
        mock.sync_result = AsyncMock()
        mock.booking_raw = AsyncMock()
        yield mock


# ── HTTP test client ──────────────────────────────────────────────────────────

@pytest.fixture
async def client(db: AsyncSession):
    from app.core import tenant as tenant_module

    async def override_get_db():
        yield db

    async def override_get_tenant_db():
        yield db

    async def override_get_current_user_id():
        return FAKE_USER_ID

    async def override_get_tenant_id():
        return FAKE_TENANT_ID

    async def override_raw_token():
        return FAKE_TOKEN

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[tenant_module.get_tenant_db] = override_get_tenant_db
    app.dependency_overrides[tenant_module.get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[tenant_module.get_tenant_id_from_token] = override_get_tenant_id
    app.dependency_overrides[tenant_module.oauth2_scheme] = override_raw_token

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── ORM factories ─────────────────────────────────────────────────────────────

async def make_channel(
    session: AsyncSession,
    *,
    ota_code: str = "booking_com",
    display_name: str = "Booking.com",
    status: str = "connected",
    consecutive_failures: int = 0,
    is_active: bool = True,
    credentials: dict | None = None,
    config: dict | None = None,
) -> Channel:
    from app.core.crypto import encrypt_credentials

    creds = credentials or {"api_key": "test-key", "hotel_id": "HTL001"}
    channel = Channel(
        ota_code=ota_code,
        display_name=display_name,
        credentials_ref=encrypt_credentials(creds),
        status=status,
        consecutive_failures=consecutive_failures,
        config=config or {},
        is_active=is_active,
    )
    session.add(channel)
    await session.flush()
    await session.refresh(channel)
    return channel


async def make_mapping(
    session: AsyncSession,
    channel_id: uuid.UUID,
    *,
    internal_room_type_id: uuid.UUID | None = None,
    ota_room_type_id: str = "RT_STANDARD",
    internal_rate_plan_id: uuid.UUID | None = None,
    ota_rate_plan_id: str = "RP_BAR",
    is_active: bool = True,
) -> ChannelMapping:
    mapping = ChannelMapping(
        channel_id=channel_id,
        internal_room_type_id=internal_room_type_id or uuid.uuid4(),
        ota_room_type_id=ota_room_type_id,
        internal_rate_plan_id=internal_rate_plan_id or uuid.uuid4(),
        ota_rate_plan_id=ota_rate_plan_id,
        is_active=is_active,
    )
    session.add(mapping)
    await session.flush()
    await session.refresh(mapping)
    return mapping
