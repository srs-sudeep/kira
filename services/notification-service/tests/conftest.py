"""pytest fixtures for notification-service tests."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all ORM models on Base.metadata
from app.database import Base, get_db
from app.main import app
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_notification_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

FAKE_TENANT_ID = uuid.uuid4()
FAKE_USER_ID = uuid.uuid4()
FAKE_TOKEN = "fake-bearer-token"
OTHER_USER_ID = uuid.uuid4()


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


# ── Email task mock ───────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def mock_email_tasks():
    with (
        patch("app.tasks.email_sender.send_new_booking_alert") as m1,
        patch("app.tasks.email_sender.send_cancellation_alert") as m2,
        patch("app.tasks.email_sender.send_channel_failure_alert") as m3,
    ):
        m1.delay = MagicMock()
        m2.delay = MagicMock()
        m3.delay = MagicMock()
        yield {"new_booking": m1, "cancellation": m2, "channel_failure": m3}


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


async def make_notification(
    session: AsyncSession,
    user_id: uuid.UUID = None,
    *,
    type: str = "new_booking",
    title: str = "Test Notification",
    message: str = "Test message.",
    is_read: bool = False,
    data: dict = None,
) -> Notification:
    notif = Notification(
        user_id=user_id or FAKE_USER_ID,
        type=type,
        title=title,
        message=message,
        data=data or {},
        is_read=is_read,
    )
    session.add(notif)
    await session.flush()
    await session.refresh(notif)
    return notif


async def make_preference(
    session: AsyncSession,
    user_id: uuid.UUID = None,
    *,
    event_type: str = "new_booking",
    email_enabled: bool = True,
    in_app_enabled: bool = True,
) -> NotificationPreference:
    pref = NotificationPreference(
        user_id=user_id or FAKE_USER_ID,
        event_type=event_type,
        email_enabled=email_enabled,
        in_app_enabled=in_app_enabled,
    )
    session.add(pref)
    await session.flush()
    await session.refresh(pref)
    return pref
