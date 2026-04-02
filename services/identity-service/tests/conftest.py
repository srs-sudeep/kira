"""KIRA Identity Service — pytest fixtures."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import models so Base.metadata knows all tables before create_all
import app.models  # noqa: F401
from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.main import app
from app.models.user import User

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_identity_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── User factories ────────────────────────────────────────────────────────────

async def make_user(
    session: AsyncSession,
    *,
    email: str = "test@example.com",
    password: str = "TestPass123!",
    first_name: str = "Test",
    last_name: str = "User",
    role: str = "property_owner",
    tenant_id: uuid.UUID | None = None,
    mfa_enabled: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        tenant_id=tenant_id,
        mfa_enabled=mfa_enabled,
        is_active=is_active,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


@pytest.fixture
async def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def regular_user(db_session: AsyncSession, tenant_id: uuid.UUID) -> User:
    return await make_user(
        db_session, email="user@example.com", tenant_id=tenant_id
    )


@pytest.fixture
async def super_admin(db_session: AsyncSession) -> User:
    return await make_user(
        db_session,
        email="admin@kira.io",
        role="super_admin",
        tenant_id=None,
    )


def auth_headers(user: User) -> dict[str, str]:
    """Return Authorization headers with a valid access token for the given user."""
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )
    return {"Authorization": f"Bearer {token}"}
