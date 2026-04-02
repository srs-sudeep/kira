"""pytest fixtures for reservation-service tests."""
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — registers all ORM models on Base.metadata
from app.core.ari_client import AvailabilityResult
from app.database import Base, get_db
from app.main import app
from app.models.guest_profile import GuestProfile
from app.models.reservation import Reservation
from app.models.reservation_note import ReservationNote

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_reservation_test"
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
        mock.reservation_created = AsyncMock()
        mock.reservation_modified = AsyncMock()
        mock.reservation_cancelled = AsyncMock()
        yield mock


# ── ARI client mock ───────────────────────────────────────────────────────────

@pytest.fixture
def mock_ari_available():
    """ARI client that always reports availability."""
    result = AvailabilityResult(
        available=True,
        total_amount=Decimal("10000.00"),
        reason=None,
    )
    with patch("app.services.reservation_service.ari_client") as mock:
        mock.check_availability = AsyncMock(return_value=result)
        mock.adjust_inventory = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_ari_unavailable():
    """ARI client that always reports unavailability."""
    result = AvailabilityResult(
        available=False,
        total_amount=Decimal("0"),
        reason="No inventory",
    )
    with patch("app.services.reservation_service.ari_client") as mock:
        mock.check_availability = AsyncMock(return_value=result)
        mock.adjust_inventory = AsyncMock(return_value=True)
        yield mock


# ── Email task mock ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_email_tasks():
    with (
        patch("app.services.reservation_service.send_booking_confirmation") as mock_confirm,
        patch("app.services.reservation_service.send_cancellation_notice") as mock_cancel,
        patch("app.services.reservation_service.send_modification_notice") as mock_modify,
    ):
        mock_confirm.delay = MagicMock()
        mock_cancel.delay = MagicMock()
        mock_modify.delay = MagicMock()
        yield


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

async def make_guest(
    session: AsyncSession,
    *,
    first_name: str = "Alice",
    last_name: str = "Smith",
    email_hash: str | None = None,
    email_encrypted: bytes | None = None,
    phone_encrypted: bytes | None = None,
    nationality: str | None = "IN",
    preferences: dict | None = None,
) -> GuestProfile:
    guest = GuestProfile(
        first_name=first_name,
        last_name=last_name,
        email=email_encrypted,
        phone=phone_encrypted,
        email_hash=email_hash,
        nationality=nationality,
        preferences=preferences or {},
    )
    session.add(guest)
    await session.flush()
    await session.refresh(guest)
    return guest


async def make_reservation(
    session: AsyncSession,
    guest_id: uuid.UUID,
    *,
    room_type_id: uuid.UUID | None = None,
    rate_plan_id: uuid.UUID | None = None,
    check_in: date = date(2026, 6, 1),
    check_out: date = date(2026, 6, 3),
    source: str = "manual",
    status: str = "confirmed",
    total_amount: Decimal = Decimal("10000.00"),
    channel_id: uuid.UUID | None = None,
    channel_reservation_id: str | None = None,
    adults: int = 2,
    children: int = 0,
    special_requests: str | None = None,
) -> Reservation:
    import random
    import string
    conf_num = "RES-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    res = Reservation(
        confirmation_number=conf_num,
        guest_profile_id=guest_id,
        room_type_id=room_type_id or uuid.uuid4(),
        rate_plan_id=rate_plan_id or uuid.uuid4(),
        check_in=check_in,
        check_out=check_out,
        source=source,
        status=status,
        total_amount=total_amount,
        currency="INR",
        adults=adults,
        children=children,
        channel_id=channel_id,
        channel_reservation_id=channel_reservation_id,
        special_requests=special_requests,
    )
    session.add(res)
    await session.flush()
    await session.refresh(res)
    return res
