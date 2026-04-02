---
title: Adding a Feature
description: How to add a new API endpoint and frontend page to KIRA — wiring routes, navigation, and connecting to the backend.
sidebar_position: 4
---

# Adding a Feature

**What you'll learn:**
- The backend steps to add a new API endpoint
- The frontend steps to add a new page and navigation link
- What changes when a feature spans multiple services

---

## Backend: Adding a New Endpoint

The pattern is always: **schema → model (if needed) → repository → service → router**.

### Example: Add a "pricing rule audit log" endpoint to rate-inventory-service

**Step 1: Define the schema** (`app/schemas/pricing_audit_schemas.py`)

```python
from pydantic import BaseModel
import uuid
from datetime import date, datetime

class PricingAuditEntry(BaseModel):
    id: uuid.UUID
    rate_plan_id: uuid.UUID
    changed_by: uuid.UUID
    changed_at: datetime
    field_name: str
    old_value: str | None
    new_value: str

    model_config = {"from_attributes": True}

class PricingAuditListResponse(BaseModel):
    items: list[PricingAuditEntry]
    total: int
    page: int
    page_size: int
```

**Step 2: Add the model** (if the table is new — skip if querying an existing table)

```python
# app/models/pricing_audit.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid

class PricingAuditLog(Base):
    __tablename__ = "pricing_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_plan_id = Column(UUID(as_uuid=True), ForeignKey("rate_plans.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False)
    field_name = Column(String, nullable=False)
    old_value = Column(String)
    new_value = Column(String, nullable=False)
```

**Step 3: Generate the Alembic migration**

```bash
cd services/rate-inventory-service
uv run alembic revision --autogenerate -m "add pricing audit log table"
# Review the generated migration in alembic/versions/
uv run alembic upgrade head
```

**Step 4: Add the repository method**

```python
# app/repositories/pricing_audit_repository.py
class PricingAuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_rate_plan(
        self,
        rate_plan_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[PricingAuditLog], int]:
        query = (
            select(PricingAuditLog)
            .where(PricingAuditLog.rate_plan_id == rate_plan_id)
            .order_by(PricingAuditLog.changed_at.desc())
        )
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        items = (await self.session.scalars(
            query.offset((page - 1) * page_size).limit(page_size)
        )).all()
        return list(items), total or 0
```

**Step 5: Add the service method**

```python
# app/services/pricing_audit_service.py
class PricingAuditService:
    async def get_audit_log(
        self,
        rate_plan_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> PricingAuditListResponse:
        items, total = await self.repo.get_by_rate_plan(rate_plan_id, page, page_size)
        return PricingAuditListResponse(
            items=[PricingAuditEntry.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )
```

**Step 6: Add the router endpoint**

```python
# app/routers/inventory_router.py (or a new audit_router.py)
@router.get(
    "/inventory/pricing-audit",
    response_model=PricingAuditListResponse,
)
async def get_pricing_audit(
    rate_plan_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: PricingAuditService = Depends(get_pricing_audit_service),
    _: User = Depends(require_roles("super_admin", "property_owner", "revenue_manager")),
) -> PricingAuditListResponse:
    return await service.get_audit_log(rate_plan_id, page, page_size)
```

**Step 7: Register the router in `main.py`** (if it's a new router file)

```python
from app.routers.audit_router import router as audit_router
app.include_router(audit_router, prefix="/api/v1")
```

---

## Frontend: Adding a New Page

### Example: Pricing audit log page

**Step 1: Add the service call** (`src/features/rates/services/pricing-audit-service.ts`)

```typescript
import { apiClient } from "@/lib/api-client";

export interface PricingAuditEntry {
  id: string;
  rate_plan_id: string;
  changed_by: string;
  changed_at: string;
  field_name: string;
  old_value: string | null;
  new_value: string;
}

export interface PricingAuditListResponse {
  items: PricingAuditEntry[];
  total: number;
  page: number;
  page_size: number;
}

export const pricingAuditService = {
  list: (ratePlanId: string, page = 1) =>
    apiClient.get<PricingAuditListResponse>(
      `/inventory/pricing-audit?rate_plan_id=${ratePlanId}&page=${page}`
    ),
};
```

**Step 2: Add the query hook** (`src/features/rates/hooks/use-pricing-audit.ts`)

```typescript
import { useQuery } from "@tanstack/react-query";
import { pricingAuditService } from "../services/pricing-audit-service";

export function usePricingAudit(ratePlanId: string, page: number) {
  return useQuery({
    queryKey: ["pricing-audit", ratePlanId, page],
    queryFn: () => pricingAuditService.list(ratePlanId, page),
    enabled: !!ratePlanId,
  });
}
```

**Step 3: Build the page component** (`src/features/rates/components/pricing-audit-page.tsx`)

```typescript
import { usePricingAudit } from "../hooks/use-pricing-audit";
import { DataTable } from "@/components/shared/data-table";
import { columns } from "./pricing-audit-columns";

interface PricingAuditPageProps {
  ratePlanId: string;
}

export function PricingAuditPage({ ratePlanId }: PricingAuditPageProps) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = usePricingAudit(ratePlanId, page);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <h2>Pricing Audit Log</h2>
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        pagination={{ total: data?.total, page, onPageChange: setPage }}
      />
    </div>
  );
}
```

**Step 4: Add the route** (in `src/app/router.tsx` or equivalent)

```typescript
{
  path: "/rates/:ratePlanId/audit",
  element: <PricingAuditPage />,
}
```

**Step 5: Add navigation link**

Add to the sidebar or as a tab in the rate plan detail view:

```typescript
<Link to={`/rates/${ratePlanId}/audit`}>
  <Button variant="outline" size="sm">Audit Log</Button>
</Link>
```

---

## Cross-Service Features

If a feature requires coordination across services:

| Need | Approach |
|---|---|
| Service A needs data owned by Service B | Service A calls Service B's REST API (internal call via K8s DNS) |
| Service A must react to something Service B does | Service B publishes a Kafka event; Service A consumes it |
| New data type shared between services | Add a schema to `shared/schemas/` |

### Adding a new Kafka event

1. Add the event schema to `shared/schemas/events.py`:

```python
class PricingRuleChangedEvent(KiraEvent):
    event_type: Literal["pricing_rule.changed"] = "pricing_rule.changed"
    payload: PricingRuleChangedPayload
```

2. Publish from the producing service:

```python
await kafka_producer.publish("pricing_rule.changed", event.model_dump())
```

3. Add a consumer in the consuming service:
   - Add the topic to `KAFKA_TOPICS` in the consumer's config
   - Add a handler function to the Kafka consumer router
   - Add the topic to the service's `_category_.json` in the consumer group docs

4. Document the event in the [Event-Driven Architecture](../architecture/event-driven.md) page.
