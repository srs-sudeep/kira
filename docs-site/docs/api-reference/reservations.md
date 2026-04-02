---
sidebar_position: 4
---

# Reservations API

Base path: `/bookings/` (via Kong) or `http://localhost:8003/` (direct)

## GET /reservations/

List reservations with optional filters.

**Query params:**

| Param | Type | Description |
|---|---|---|
| `status` | string | `confirmed` \| `checked_in` \| `checked_out` \| `cancelled` \| `no_show` |
| `channel` | string | `direct` \| `booking_com` \| `expedia` \| `mmt` |
| `check_in_from` | date | Filter by check-in date start |
| `check_in_to` | date | Filter by check-in date end |
| `search` | string | Search by guest name, email, or confirmation number |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "confirmation_number": "KIRA-2025-00042",
      "channel": "booking_com",
      "channel_confirmation_id": "4123456789",
      "guest": {
        "id": "uuid",
        "full_name": "Jane Smith",
        "email": "jane@example.com"
      },
      "room_type": { "id": "uuid", "name": "Deluxe King", "code": "DLX-K" },
      "rate_plan": { "id": "uuid", "name": "Best Available Rate" },
      "check_in": "2025-06-15",
      "check_out": "2025-06-18",
      "nights": 3,
      "adults": 2,
      "children": 0,
      "room_rate": "150.00",
      "total_amount": "450.00",
      "currency": "USD",
      "status": "confirmed",
      "created_at": "2025-05-20T14:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

## POST /reservations/

Create a reservation (typically called by channel-engine for OTA bookings, or directly for walk-ins).

```json
{
  "channel": "direct",
  "guest": {
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1-555-0100",
    "country": "US"
  },
  "room_type_id": "uuid",
  "rate_plan_id": "uuid",
  "check_in": "2025-07-01",
  "check_out": "2025-07-05",
  "adults": 2,
  "children": 1,
  "special_requests": "High floor requested"
}
```

## GET /reservations/{id}

Full reservation detail including modification history.

## PATCH /reservations/{id}

Modify a confirmed reservation.

```json
{
  "check_in": "2025-07-02",
  "check_out": "2025-07-06",
  "room_type_id": "uuid",
  "special_requests": "Early check-in requested"
}
```

## POST /reservations/{id}/cancel

```json
{
  "reason": "guest_request",
  "notes": "Guest called to cancel due to travel changes"
}
```

**Response 200:**
```json
{
  "reservation_id": "uuid",
  "status": "cancelled",
  "refund_amount": "300.00",
  "refund_currency": "USD",
  "cancellation_policy_applied": "48h"
}
```

## POST /reservations/{id}/check-in

Mark reservation as checked in. Returns `204 No Content`.

## POST /reservations/{id}/check-out

Mark reservation as checked out. Returns `204 No Content`.
