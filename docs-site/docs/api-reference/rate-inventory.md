---
sidebar_position: 3
---

# Rate & Inventory API

Base path: `/rates/` (via Kong) or `http://localhost:8002/` (direct)

## Room Types

### GET /room-types/

List all room types.

**Response 200:**
```json
[
  {
    "id": "uuid",
    "name": "Deluxe King",
    "code": "DLX-K",
    "description": "Spacious room with king bed and city view",
    "max_occupancy": 2,
    "base_occupancy": 2,
    "amenities": ["wifi", "air_conditioning", "minibar", "safe"],
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

### POST /room-types/

```json
{
  "name": "Deluxe King",
  "code": "DLX-K",
  "description": "Spacious room with king bed",
  "max_occupancy": 2,
  "base_occupancy": 2,
  "amenities": ["wifi", "air_conditioning"]
}
```

---

## Rate Plans

### GET /rate-plans/

Query params: `room_type_id` (optional filter)

### POST /rate-plans/

```json
{
  "room_type_id": "uuid",
  "name": "Best Available Rate",
  "code": "BAR",
  "meal_plan": "room_only",
  "cancellation_policy": "free"
}
```

`meal_plan` values: `room_only` | `bed_breakfast` | `half_board` | `full_board`  
`cancellation_policy` values: `free` | `non_refundable` | `24h` | `48h` | `72h`

---

## ARI Calendar

### GET /ari/

Get ARI data for a date range.

**Query params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `room_type_id` | UUID | Yes | Room type |
| `rate_plan_id` | UUID | Yes | Rate plan |
| `from_date` | date | Yes | Start date (YYYY-MM-DD) |
| `to_date` | date | Yes | End date (YYYY-MM-DD, max 90 days) |

**Response 200:**
```json
[
  {
    "date": "2025-06-01",
    "available_rooms": 5,
    "rate": "150.00",
    "min_stay": 1,
    "max_stay": null,
    "closed_to_arrival": false,
    "closed_to_departure": false,
    "stop_sell": false
  }
]
```

### PUT /ari/bulk-update

Apply ARI changes across a date range.

```json
{
  "room_type_id": "uuid",
  "rate_plan_id": "uuid",
  "from_date": "2025-06-01",
  "to_date": "2025-06-30",
  "days_of_week": [1, 2, 3, 4, 5],
  "updates": {
    "rate": 175.00,
    "available_rooms": 4,
    "min_stay": 2,
    "stop_sell": false
  }
}
```

`days_of_week`: 1=Monday ... 7=Sunday. Omit to apply to all days.  
All fields in `updates` are optional — only provided fields are changed.

**Response 200:**
```json
{
  "updated_dates": 22,
  "message": "ARI updated successfully. Channel sync initiated."
}
```

### GET /ari/availability

Check room availability for a stay.

**Query params:** `room_type_id`, `check_in` (YYYY-MM-DD), `check_out` (YYYY-MM-DD)

**Response 200:**
```json
{
  "available": true,
  "min_available_rooms": 3,
  "nights": 3,
  "total_rate": "450.00",
  "restrictions": {
    "min_stay_met": true,
    "closed_to_arrival": false,
    "stop_sell": false
  }
}
```
