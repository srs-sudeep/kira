---
sidebar_position: 5
---

# Channels API

Base path: `/channels/` (via Kong) or `http://localhost:8004/` (direct)

## GET /channels/

List all connected OTA channels.

**Response 200:**
```json
[
  {
    "id": "uuid",
    "name": "Booking.com - Grand Hotel",
    "ota": "booking_com",
    "is_active": true,
    "last_sync_at": "2025-06-15T09:00:00Z",
    "sync_status": "active",
    "error_message": null,
    "mapping_count": 6,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

`ota` values: `booking_com` | `expedia` | `mmt`  
`sync_status` values: `active` | `error` | `paused`

## POST /channels/

Connect a new OTA channel.

```json
{
  "name": "Booking.com - Grand Hotel",
  "ota": "booking_com",
  "credentials": {
    "username": "hotel_user",
    "password": "hotel_pass",
    "hotel_id": "123456"
  }
}
```

Credentials structure varies by OTA:

| OTA | Required credential fields |
|---|---|
| `booking_com` | `username`, `password`, `hotel_id` |
| `expedia` | `api_key`, `api_secret`, `hotel_id` |
| `mmt` | `api_key`, `api_secret`, `hotel_code` |

## POST /channels/{id}/test

Test the OTA connection.

**Response 200:**
```json
{
  "success": true,
  "message": "Connection successful",
  "hotel_name": "Grand Hotel (Booking.com ID: 123456)"
}
```

**Response 200 (failed):**
```json
{
  "success": false,
  "message": "Authentication failed: Invalid credentials"
}
```

## POST /channels/{id}/sync-now

Trigger an immediate full ARI push to the OTA.

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "message": "Full sync initiated. Check sync log for progress."
}
```

## GET /channels/{id}/mappings

List room type / rate plan mappings for this channel.

**Response 200:**
```json
[
  {
    "id": "uuid",
    "room_type": { "id": "uuid", "name": "Deluxe King", "code": "DLX-K" },
    "rate_plan": { "id": "uuid", "name": "Best Available Rate", "code": "BAR" },
    "ota_room_id": "bcom_room_123",
    "ota_rate_id": "bcom_rate_456",
    "is_active": true
  }
]
```

## POST /channels/{id}/mappings

```json
{
  "room_type_id": "uuid",
  "rate_plan_id": "uuid",
  "ota_room_id": "bcom_room_123",
  "ota_rate_id": "bcom_rate_456"
}
```

## GET /channels/{id}/sync-log

Paginated sync history.

**Query params:** `page`, `page_size`, `status` (`success` | `failed` | `partial`)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "operation": "ari_push",
      "status": "success",
      "dates_pushed": 30,
      "error_message": null,
      "started_at": "2025-06-15T09:00:00Z",
      "completed_at": "2025-06-15T09:00:05Z",
      "duration_ms": 5243
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```
