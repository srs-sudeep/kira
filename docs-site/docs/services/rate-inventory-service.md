---
sidebar_position: 2
---

# Rate & Inventory Service

Manages room types, rate plans, and the ARI (Availability, Rates, Inventory) calendar. Runs on port **8002**.

## Responsibilities

- Define room types with capacity, amenities, and base occupancy
- Create rate plans (BAR, corporate, package) with meal plans and cancellation policies
- Maintain per-day ARI data: available rooms, rate, min/max stay, stop-sell flags
- Bulk updates across date ranges
- Publish `ari.updated` Kafka events when rates or availability change

## Key Endpoints

### Room Types

| Method | Path | Description |
|---|---|---|
| `GET` | `/room-types/` | List room types |
| `POST` | `/room-types/` | Create room type |
| `GET` | `/room-types/{id}` | Get room type |
| `PATCH` | `/room-types/{id}` | Update room type |
| `DELETE` | `/room-types/{id}` | Delete room type |

### Rate Plans

| Method | Path | Description |
|---|---|---|
| `GET` | `/rate-plans/` | List rate plans |
| `POST` | `/rate-plans/` | Create rate plan |
| `GET` | `/rate-plans/{id}` | Get rate plan |
| `PATCH` | `/rate-plans/{id}` | Update rate plan |

### ARI Calendar

| Method | Path | Description |
|---|---|---|
| `GET` | `/ari/` | Get ARI for date range (query: room_type_id, rate_plan_id, from_date, to_date) |
| `PUT` | `/ari/bulk-update` | Bulk update ARI for date range |
| `GET` | `/ari/availability` | Check availability for check-in/out dates |

## Data Models

### RoomType

```python
class RoomType(Base):
    id: UUID
    name: str                 # e.g., "Deluxe King"
    code: str                 # e.g., "DLX-K"
    description: str | None
    max_occupancy: int
    base_occupancy: int
    amenities: list[str]      # JSONB
    is_active: bool
    created_at: datetime
```

### RatePlan

```python
class RatePlan(Base):
    id: UUID
    room_type_id: UUID
    name: str                 # e.g., "Best Available Rate"
    code: str                 # e.g., "BAR"
    meal_plan: MealPlan       # room_only | bed_breakfast | half_board | full_board
    cancellation_policy: CancellationPolicy  # free | non_refundable | 24h | 48h | 72h
    is_active: bool
```

### ARICalendar

```python
class ARICalendar(Base):
    id: UUID
    room_type_id: UUID
    rate_plan_id: UUID
    date: date
    available_rooms: int
    rate: Decimal             # per night
    min_stay: int             # minimum nights
    max_stay: int | None
    closed_to_arrival: bool
    closed_to_departure: bool
    stop_sell: bool
```

## Bulk Update Request

```json
{
  "room_type_id": "uuid",
  "rate_plan_id": "uuid",
  "from_date": "2025-06-01",
  "to_date": "2025-06-30",
  "days_of_week": [1, 2, 3, 4, 5],
  "updates": {
    "rate": 150.00,
    "available_rooms": 5,
    "min_stay": 2,
    "stop_sell": false
  }
}
```

## Kafka Events Published

After any ARI update, the service publishes:

```python
await kafka_producer.send("ari.updated", {
    "event_type": "ari.updated",
    "tenant_id": str(tenant_id),
    "room_type_id": str(room_type_id),
    "rate_plan_id": str(rate_plan_id),
    "date_range": {"start": from_date, "end": to_date},
    "changes": list(updates.keys()),
    "timestamp": datetime.utcnow().isoformat(),
})
```
