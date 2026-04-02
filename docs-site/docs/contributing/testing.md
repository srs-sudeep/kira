---
sidebar_position: 3
---

# Testing

## Backend Testing

### Stack

- **pytest** with `pytest-asyncio` for async tests
- **httpx** `AsyncClient` for testing FastAPI endpoints
- **factory_boy** for test data factories
- **pytest-cov** for coverage measurement

### Test Structure

```
services/{name}/tests/
├── conftest.py          # shared fixtures (db session, test client, auth headers)
├── test_routers/        # integration tests: HTTP → response
│   ├── test_auth.py
│   └── test_room_types.py
├── test_services/       # unit tests: service method → outcome
│   └── test_rate_service.py
└── test_repositories/   # unit tests: repository → DB query result
    └── test_rate_repo.py
```

### Conftest Pattern

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine, Base

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

@pytest.fixture
def auth_headers(test_token: str):
    return {"Authorization": f"Bearer {test_token}"}
```

### Writing Tests

```python
# tests/test_routers/test_room_types.py
async def test_create_room_type(client, auth_headers):
    response = await client.post(
        "/room-types/",
        json={
            "name": "Deluxe King",
            "code": "DLX-K",
            "max_occupancy": 2,
            "base_occupancy": 2,
            "amenities": ["wifi"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Deluxe King"
    assert "id" in data

async def test_create_room_type_duplicate_code(client, auth_headers, existing_room_type):
    response = await client.post(
        "/room-types/",
        json={"name": "Another Room", "code": "DLX-K", ...},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["code"] == "ROOM_TYPE_CODE_EXISTS"
```

### Coverage Target

Minimum 70% coverage on `app/` code. Focus coverage on:
- All service methods (business logic)
- All router happy paths
- All error/edge cases in services

Don't chase coverage on configuration files, `main.py`, or migration files.

## Frontend Testing

Frontend testing uses:
- **Vitest** — test runner
- **React Testing Library** — component rendering
- **MSW (Mock Service Worker)** — API mocking

```bash
cd web-app
bun run test          # run tests
bun run test:coverage # with coverage
```

### Component Test Example

```tsx
import { render, screen } from '@testing-library/react';
import { ReservationStatusBadge } from './ReservationStatusBadge';

test('shows correct color for confirmed status', () => {
  render(<ReservationStatusBadge status="confirmed" />);
  const badge = screen.getByText('Confirmed');
  expect(badge).toHaveClass('bg-green-100');
});
```
