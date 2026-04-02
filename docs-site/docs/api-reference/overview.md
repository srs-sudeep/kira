---
sidebar_position: 1
---

# API Reference Overview

All KIRA services expose REST APIs following consistent conventions.

## Base URLs

| Environment | Base URL |
|---|---|
| Local (via Kong) | `http://localhost:8000` |
| Local (direct) | `http://localhost:800{1-6}` |
| Staging | `https://api.staging.kira.abodeab.com` |
| Production | `https://api.kira.abodeab.com` |

## Authentication

All endpoints (except `/auth/login` and `/auth/register`) require a JWT Bearer token:

```http
Authorization: Bearer <access_token>
```

Access tokens expire after 60 minutes. Use `POST /identity/auth/refresh` with the refresh token (HttpOnly cookie) to get a new access token.

## Request Format

- `Content-Type: application/json`
- Request bodies are Pydantic-validated — extra fields are ignored
- All UUIDs as lowercase hyphenated strings: `550e8400-e29b-41d4-a716-446655440000`
- Dates as ISO 8601: `2025-06-15`
- Datetimes as ISO 8601 UTC: `2025-06-15T10:30:00Z`
- Monetary amounts as numbers with 2 decimal places: `150.00`

## Response Format

### Success

```json
{
  "id": "uuid",
  "name": "Deluxe King",
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Paginated List

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### Error

```json
{
  "detail": "Rate plan not found",
  "code": "RATE_PLAN_NOT_FOUND"
}
```

Validation errors (422):

```json
{
  "detail": [
    {
      "loc": ["body", "max_occupancy"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```

## HTTP Status Codes

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `204` | No Content (successful DELETE) |
| `400` | Bad Request (business logic error) |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (insufficient role) |
| `404` | Not Found |
| `409` | Conflict (duplicate) |
| `422` | Unprocessable Entity (validation error) |
| `429` | Too Many Requests (rate limited) |
| `500` | Internal Server Error |

## Interactive Docs

Each service exposes Swagger UI and ReDoc:

```
http://localhost:8001/docs    # identity-service Swagger
http://localhost:8001/redoc   # identity-service ReDoc

http://localhost:8002/docs    # rate-inventory-service Swagger
# ... etc for 8003, 8004, 8005, 8006
```

## Rate Limiting

Rate limiting is enforced at the Kong gateway level:
- **Default:** 100 requests/minute per IP
- **Auth endpoints:** 10 requests/minute per IP (brute-force protection)
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
