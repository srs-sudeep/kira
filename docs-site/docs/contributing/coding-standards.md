---
title: Coding Standards
description: Python ruff rules, async patterns, type hints, and TypeScript strict mode conventions for KIRA.
sidebar_position: 2
---

# Coding Standards

**What you'll learn:**
- Python: ruff configuration, required async patterns, type hints
- TypeScript: strict mode rules, component patterns, no-any enforcement
- Testing conventions that apply to both

---

## Python Standards

### Linting and formatting: ruff

All Python services use `ruff` for both linting and formatting. The config is in each service's `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ANN",  # flake8-annotations (type hints required)
    "S",    # flake8-bandit (security)
    "ASYNC",# flake8-async (async patterns)
]
ignore = ["ANN101", "ANN102"]  # self and cls don't need type hints
```

Run before committing:

```bash
uv run ruff check .        # lint
uv run ruff format --check .  # check formatting
uv run ruff format .          # auto-format
```

### Async patterns

All I/O must be async. Never use blocking calls in async functions:

```python
# ✅ Correct
async def get_reservation(reservation_id: uuid.UUID) -> Reservation:
    async with get_session() as session:
        repo = ReservationRepository(session)
        return await repo.get_by_id(reservation_id)

# ❌ Wrong — blocks the event loop
def get_reservation(reservation_id: uuid.UUID) -> Reservation:
    with Session() as session:
        return session.get(Reservation, reservation_id)

# ❌ Wrong — blocking HTTP call in async context
async def push_to_ota(data: dict) -> None:
    response = requests.post(url, json=data)  # use httpx.AsyncClient instead
```

Always use:
- `httpx.AsyncClient` for outbound HTTP (never `requests`)
- `asyncpg` / `asyncio` for database (never `psycopg2` synchronously)
- `aiokafka` for Kafka (never `confluent-kafka` blocking API)

### Type hints

All function signatures must have type hints. Use Python 3.10+ union syntax:

```python
# ✅ Correct
async def create_reservation(
    data: ReservationCreate,
    tenant_id: str,
    current_user: User,
) -> Reservation:

# ✅ Optional parameter
async def get_reservations(
    status: ReservationStatus | None = None,
    page: int = 1,
) -> list[Reservation]:

# ❌ Wrong — missing return type
async def update_channel(channel_id: uuid.UUID, data: ChannelUpdate):
```

### Layer rules

The Router → Service → Repository pattern is enforced:

```python
# router — validate input, call service, return response
@router.post("/reservations", status_code=201)
async def create_reservation(
    data: ReservationCreate,
    service: ReservationService = Depends(get_reservation_service),
    current_user: User = Depends(get_current_user),
) -> ReservationResponse:
    reservation = await service.create(data, current_user.tenant_id)
    return ReservationResponse.model_validate(reservation)

# service — business logic, calls repository, publishes events
class ReservationService:
    async def create(self, data: ReservationCreate, tenant_id: str) -> Reservation:
        # business validation
        await self._validate_no_duplicate(data)
        reservation = await self.repo.create(data)
        await self.kafka_producer.publish("reservation.created", {...})
        return reservation

# repository — database queries only
class ReservationRepository:
    async def create(self, data: ReservationCreate) -> Reservation:
        reservation = Reservation(**data.model_dump())
        self.session.add(reservation)
        await self.session.flush()
        await self.session.refresh(reservation)
        return reservation
```

Violations of this pattern:
- Routers calling `session.execute()` directly → move to repository
- Services importing from other services' modules → use REST or Kafka instead
- Repositories calling `httpx` → that belongs in a service

### Configuration

All config via Pydantic `BaseSettings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env.local"
        case_sensitive = False

settings = Settings()
```

Never use `os.environ.get()` directly in business logic. Never hardcode defaults that look like real secrets (use `"change-me-in-production"` only as a last resort, with a startup warning).

### Custom exceptions

```python
# exceptions.py
class KiraBaseException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(KiraBaseException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} {resource_id} not found", status_code=404)

class PermissionDeniedError(KiraBaseException):
    def __init__(self):
        super().__init__("Permission denied", status_code=403)
```

Raise these in service layer. The global exception handler in `exception_handlers.py` converts them to JSON responses.

---

## TypeScript Standards

### Strict mode

All TypeScript is compiled with `strict: true`. This means:
- `noImplicitAny: true` — **no `any` types**
- `strictNullChecks: true` — null/undefined must be handled explicitly
- `noUncheckedIndexedAccess: true` — array access returns `T | undefined`

If you genuinely need to work with an unknown shape (e.g., parsing an external API response), use `unknown` and narrow it:

```typescript
// ✅ Correct
function parseResponse(data: unknown): ApiResponse {
  if (!isApiResponse(data)) throw new Error("Invalid response shape");
  return data;
}

// ❌ Wrong
function parseResponse(data: any): ApiResponse {
  return data as ApiResponse;
}
```

### Component conventions

```typescript
// PascalCase component name
// Props interface in the same file
// No default export (use named exports)

interface ReservationCardProps {
  reservation: Reservation;
  onCancel: (id: string) => void;
}

export function ReservationCard({ reservation, onCancel }: ReservationCardProps) {
  return (
    <Card>
      <CardHeader>{reservation.confirmation_number}</CardHeader>
      {/* ... */}
    </Card>
  );
}
```

### Server state vs. client state

| State type | Tool | When |
|---|---|---|
| Server data (API responses) | TanStack Query | Room types, reservations, channels — anything that lives in the backend |
| Client/UI state | Zustand | Auth tokens, theme, sidebar open/closed |
| Form state | React Hook Form + Zod | All form inputs |

Never store API response data in Zustand. Never fetch data with `useEffect + fetch`.

```typescript
// ✅ Correct — TanStack Query for server data
function useReservations(filters: ReservationFilters) {
  return useQuery({
    queryKey: ["reservations", filters],
    queryFn: () => reservationService.list(filters),
  });
}

// ❌ Wrong — manual fetch in useEffect
function ReservationList() {
  const [reservations, setReservations] = useState([]);
  useEffect(() => {
    fetch("/api/reservations").then(r => r.json()).then(setReservations);
  }, []);
}
```

### shadcn/ui components

Use shadcn/ui for all base UI elements. Never write raw HTML `<input>`, `<button>`, `<select>`:

```typescript
// ✅ Correct
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// ❌ Wrong
<button onClick={handleClick}>Submit</button>
<input type="text" value={value} onChange={...} />
```

### File naming

```
kebab-case for files:         reservation-card.tsx, use-channels.ts
PascalCase for components:    ReservationCard, ChannelTable
camelCase for functions:      fetchReservations, parseAriCalendar
SCREAMING_SNAKE for constants: MAX_RETRY_ATTEMPTS, DEFAULT_PAGE_SIZE
```

Feature modules live in `src/features/<name>/`:

```
src/features/reservations/
├── components/
│   ├── reservation-card.tsx
│   └── reservation-table.tsx
├── hooks/
│   └── use-reservations.ts
├── services/
│   └── reservation-service.ts
└── types.ts
```
