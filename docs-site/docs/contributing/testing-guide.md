---
title: Testing Guide
description: Backend pytest patterns, fixture conventions, service-layer testing, and integration testing with FastAPI TestClient.
sidebar_position: 5
---

# Testing Guide

**What you'll learn:**

- What to test and what to skip
- pytest fixtures and how to structure them
- How to test services by mocking repositories
- How to write integration tests using FastAPI's TestClient
- Frontend testing with Vitest and React Testing Library (when added)

---

## What to Test

| Layer                    | What to test                                          | What to skip                                       |
| ------------------------ | ----------------------------------------------------- | -------------------------------------------------- |
| Service (business logic) | Business rules, error cases, Kafka publish calls      | Dependency injection wiring                        |
| Repository               | Query correctness with a real test DB                 | SQLAlchemy internals                               |
| Router (integration)     | Request validation, auth enforcement, response schema | Internal business logic (tested via service tests) |
| Models                   | Non-trivial property methods                          | Plain attribute access                             |

**Coverage target: 70% on the `app/services/` and `app/repositories/` modules.** Router tests and model tests are bonuses, not the target.

:::tip Test behaviour, not implementation
A good test verifies observable outputs for given inputs. A bad test verifies that a specific internal method was called a specific number of times. The latter breaks on every refactor.
:::

---

## pytest Configuration

Each service's `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
env = [
    "ENVIRONMENT=test",
    "DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kira_identity_test",
    "REDIS_URL=redis://localhost:6379/0",
    "SECRET_KEY=test-secret-key",
    "JWT_SECRET_KEY=test-jwt-secret",
]
```

`asyncio_mode = "auto"` means all `async def test_*` functions are automatically treated as coroutines — no `@pytest.mark.asyncio` decorator needed.

---

## Fixtures

### Database session fixture

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/kira_identity_test"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def session(engine) -> AsyncSession:
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()   # each test is isolated
```

The `session.rollback()` at the end of each test ensures tests don't bleed into each other — every test starts with a clean state.

### Repository fixture

```python
@pytest.fixture
async def reservation_repo(session: AsyncSession) -> ReservationRepository:
    return ReservationRepository(session)
```

### Service fixture with mocked repository

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_reservation_repo() -> MagicMock:
    return MagicMock(spec=ReservationRepository)

@pytest.fixture
def mock_kafka_producer() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def reservation_service(mock_reservation_repo, mock_kafka_producer) -> ReservationService:
    return ReservationService(
        repo=mock_reservation_repo,
        kafka_producer=mock_kafka_producer,
    )
```

### TestClient fixture (integration tests)

```python
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

@pytest.fixture
def auth_headers(test_user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {test_user_token}"}
```

---

## Testing Services

Service tests mock the repository layer. Test the business logic, not the SQL.

```python
# tests/test_reservation_service.py
import pytest
from datetime import date
from unittest.mock import AsyncMock
from app.services.reservation_service import ReservationService
from app.schemas.reservation_schemas import ReservationCreate
from app.exceptions import ConflictError

class TestCreateReservation:
    async def test_creates_and_publishes_event(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MagicMock,
        mock_kafka_producer: AsyncMock,
    ):
        data = ReservationCreate(
            room_type_id="...",
            check_in=date(2026, 5, 1),
            check_out=date(2026, 5, 3),
            guest_name="Alice Smith",
        )
        mock_reservation_repo.create = AsyncMock(return_value=FakeReservation(id="r_1"))
        mock_reservation_repo.find_duplicate = AsyncMock(return_value=None)

        result = await reservation_service.create(data, tenant_id="t_abc")

        assert result.id == "r_1"
        mock_kafka_producer.publish.assert_called_once_with(
            "reservation.created",
            pytest.approx({"reservation_id": "r_1", "tenant_id": "t_abc"}, partial=True),
        )

    async def test_raises_conflict_for_duplicate(
        self,
        reservation_service: ReservationService,
        mock_reservation_repo: MagicMock,
    ):
        mock_reservation_repo.find_duplicate = AsyncMock(return_value=FakeReservation())

        with pytest.raises(ConflictError):
            await reservation_service.create(data, tenant_id="t_abc")
```

---

## Testing Repositories

Repository tests use a real database. They verify that queries return the right data.

```python
# tests/test_reservation_repository.py
class TestReservationRepository:
    async def test_get_by_id_returns_reservation(
        self,
        reservation_repo: ReservationRepository,
        session: AsyncSession,
    ):
        # Arrange — insert directly into test DB
        reservation = Reservation(
            id=uuid.uuid4(),
            confirmation_number="KIRA-001",
            status="confirmed",
        )
        session.add(reservation)
        await session.flush()

        # Act
        result = await reservation_repo.get_by_id(reservation.id)

        # Assert
        assert result is not None
        assert result.confirmation_number == "KIRA-001"

    async def test_get_by_id_returns_none_for_missing(
        self,
        reservation_repo: ReservationRepository,
    ):
        result = await reservation_repo.get_by_id(uuid.uuid4())
        assert result is None
```

---

## Integration Tests

Integration tests hit the full FastAPI app through TestClient. Use them for:

- Verifying auth enforcement (unauthenticated request returns 401)
- Verifying request validation (bad input returns 422 with useful errors)
- Smoke-testing the happy path end-to-end

```python
# tests/test_reservation_router.py
class TestPostReservation:
    async def test_creates_reservation(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        response = await client.post(
            "/api/v1/reservations",
            json={
                "room_type_id": str(uuid.uuid4()),
                "check_in": "2026-05-01",
                "check_out": "2026-05-03",
                "guest_name": "Bob Jones",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "confirmed"
        assert "confirmation_number" in data

    async def test_requires_authentication(self, client: AsyncClient):
        response = await client.post("/api/v1/reservations", json={})
        assert response.status_code == 401

    async def test_validates_date_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        response = await client.post(
            "/api/v1/reservations",
            json={
                "check_in": "2026-05-03",
                "check_out": "2026-05-01",   # checkout before checkin
                ...
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
```

---

## Testing Kafka Publishing

When a service publishes Kafka events, assert that the producer was called with the right topic and payload:

```python
async def test_publishes_ari_updated_event(
    rate_service: RateService,
    mock_kafka_producer: AsyncMock,
):
    await rate_service.update_ari(...)

    mock_kafka_producer.publish.assert_called_once()
    call_args = mock_kafka_producer.publish.call_args
    assert call_args[0][0] == "ari.updated"   # topic name
    payload = call_args[0][1]
    assert payload["event_type"] == "ari.updated"
    assert payload["tenant_id"] == "t_abc"
```

---

## Frontend Testing (when added)

The frontend uses **Vitest** (Jest-compatible, Vite-native) and **React Testing Library**.

### Setup

Vitest is configured in `web-app/vite.config.ts`:

```typescript
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
  include: ['src/**/*.{test,spec}.{ts,tsx}'],
}
```

The setup file (`src/test/setup.ts`) loads jest-dom matchers:

```typescript
import "@testing-library/jest-dom/vitest";
```

### Running web tests

```bash
# Via CLI
uv run kira test --web

# Or directly
cd web-app && bun run test

# Watch mode for development
cd web-app && bun run test:watch
```

### What to test on the frontend

| Test type    | What                                           | Tools                          |
| ------------ | ---------------------------------------------- | ------------------------------ |
| Unit         | Custom hooks, utility functions, service calls | Vitest + msw (mock API)        |
| Component    | Rendering, user interactions, form validation  | Vitest + React Testing Library |
| E2E (future) | Full user flows in a real browser              | Playwright                     |

### Component test pattern

```typescript
import { render, screen, userEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReservationCard } from "./reservation-card";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={new QueryClient()}>
    {children}
  </QueryClientProvider>
);

test("shows confirmation number", () => {
  render(
    <ReservationCard
      reservation={{ id: "r_1", confirmation_number: "KIRA-2026-001", status: "confirmed" }}
      onCancel={vi.fn()}
    />,
    { wrapper }
  );
  expect(screen.getByText("KIRA-2026-001")).toBeInTheDocument();
});

test("calls onCancel when cancel button clicked", async () => {
  const onCancel = vi.fn();
  render(<ReservationCard reservation={...} onCancel={onCancel} />, { wrapper });

  await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
  expect(onCancel).toHaveBeenCalledWith("r_1");
});
```

### API mocking with msw

```typescript
// tests/mocks/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/v1/reservations", () =>
    HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 }),
  ),
];
```

Use msw's `server` in `beforeAll`/`afterAll` so tests never make real HTTP calls.

---

## Running Tests via CLI

The KIRA CLI provides a unified interface for all test commands:

```bash
# Test a single backend service
uv run kira test identity-service

# Test all services + web-app
uv run kira test --all

# Web-app only
uv run kira test --web

# With coverage gate (70% minimum)
uv run kira test --coverage

# Integration tests (starts Postgres, Redis, Kafka)
uv run kira test --integration
```

Or use Makefile equivalents:

```bash
make test-identity-service     # Single service
make test-all                  # All services
make test-web                  # Web-app (Vitest)
make test-coverage             # With coverage
make test-integration          # Integration with infra
```

See the [CLI Reference](../getting-started/cli-reference.md) for the full command list.
