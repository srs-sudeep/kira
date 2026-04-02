---
sidebar_position: 2
---

# Code Conventions

## Python (Backend)

### File and Symbol Naming

- `snake_case` everywhere: files, functions, variables, module names, DB columns
- Exception: `PascalCase` for class names (SQLAlchemy models, Pydantic schemas, exceptions)

```python
# Good
class RatePlan(Base):
    rate_plan_id: UUID
    base_rate: Decimal

def calculate_refund_amount(reservation: Reservation) -> Decimal:
    ...

# Bad
class ratePlan(Base):
    ratePlanId: UUID
```

### Architecture Rules

1. **Routers are thin** — validate input (Pydantic), call one service method, return response schema. No business logic, no DB calls.

2. **Services own business logic** — call repositories, enforce rules, publish Kafka events. One method = one business operation.

3. **Repositories own queries** — all SQLAlchemy in repositories. Services never use the `db` session directly.

4. **No secrets in code** — all config from `Pydantic BaseSettings` via environment variables.

5. **Structured logging only** — `structlog.get_logger()`, no `print()`.

6. **Async everywhere** — all handlers, services, and repositories are `async def`. Use `asyncpg`, `aiokafka`, `httpx` for I/O.

### Config Pattern

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
```

### Exception Pattern

```python
# app/exceptions.py
class KiraException(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class RatePlanNotFoundError(KiraException):
    def __init__(self, rate_plan_id: str):
        super().__init__(
            message=f"Rate plan {rate_plan_id} not found",
            code="RATE_PLAN_NOT_FOUND"
        )
```

## TypeScript (Frontend)

### Naming

- `PascalCase` for components and types: `RoomTypeCard`, `ReservationFilters`
- `camelCase` for functions, hooks, variables: `useRoomTypes`, `formatCurrency`
- `kebab-case` for file names: `room-type-card.tsx`, `use-room-types.ts`
- `SCREAMING_SNAKE_CASE` for constants: `QUERY_KEYS`, `API_BASE_URL`

### No `any`

TypeScript strict mode is enabled. If you're tempted to use `any`, use `unknown` and narrow with a type guard:

```typescript
// Bad
function processData(data: any) { ... }

// Good
function processData(data: unknown) {
  if (typeof data === 'object' && data !== null && 'id' in data) {
    // narrowed to object with 'id'
  }
}
```

### Component Structure

```tsx
// Components are function declarations, not arrow functions at module level
export function RoomTypeCard({ roomType }: { roomType: RoomType }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{roomType.name}</CardTitle>
      </CardHeader>
    </Card>
  );
}
```

### shadcn/ui First

Never write raw HTML form elements. Always use shadcn/ui:

```tsx
// Good
<Button variant="outline" size="sm">Edit</Button>
<Input placeholder="Room name" {...register('name')} />
<Select>
  <SelectTrigger><SelectValue /></SelectTrigger>
  <SelectContent>...</SelectContent>
</Select>

// Bad
<button className="border px-2">Edit</button>
<input placeholder="Room name" />
```
