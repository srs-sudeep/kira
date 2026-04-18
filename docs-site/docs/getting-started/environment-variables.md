---
title: Environment Variables
sidebar_position: 4
description: Service configuration via env vars, with links to kira setup, bootstrap, and per-developer DB isolation.
---

# Environment Variables

All services read configuration from environment variables via Pydantic `BaseSettings`. Never hardcode secrets.

:::tip Getting `.env.local` files and a running stack

- **Copy envs + install + migrate + seed (host DB path):** `uv run kira dev setup` — same as **`make dev-setup`**.
- **Docker-first path** (migrate/seed inside containers): **`uv run kira dev bootstrap`** — same as **`make bootstrap`**.
- **Isolated Postgres database name per developer:** **`uv run kira dev init`** (CLI only) — see **[Per-developer database isolation](./per-developer-db.md)**.

Manual copy remains: **`cp services/<svc>/.env.example services/<svc>/.env.local`** for each service.
:::

## Shared Variables

These are set in the root `.env` and shared across services via Docker Compose:

| Variable | Example | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` \| `staging` \| `production` |
| `LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` |
| `POSTGRES_HOST` | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `kira` | DB user |
| `POSTGRES_PASSWORD` | `kira_dev_password` | DB password |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker address |
| `KAFKA_GROUP_ID_PREFIX` | `kira` | Prefix for Kafka consumer groups |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Celery results backend |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins (comma-separated) |

## Identity Service

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kira:pass@postgres:5432/kira_identity` |
| `SECRET_KEY` | 32-character random string for cookie signing |
| `JWT_SECRET_KEY` | 64-character random string for JWT signing |
| `JWT_ALGORITHM` | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |

## Rate Inventory Service

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kira:pass@postgres:5432/kira_rate_inventory` |
| `SECRET_KEY` | 32-character random string |
| `IDENTITY_SERVICE_URL` | `http://identity-service:8001` |

## Reservation Service

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kira:pass@postgres:5432/kira_reservation` |
| `SECRET_KEY` | 32-character random string |
| `IDENTITY_SERVICE_URL` | `http://identity-service:8001` |
| `RATE_INVENTORY_SERVICE_URL` | `http://rate-inventory-service:8002` |

## Channel Engine

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kira:pass@postgres:5432/kira_channel` |
| `SECRET_KEY` | 32-character random string |
| `BOOKING_COM_USERNAME` | Booking.com connectivity API username |
| `BOOKING_COM_PASSWORD` | Booking.com connectivity API password |
| `EXPEDIA_API_KEY` | Expedia EQC API key |
| `EXPEDIA_API_SECRET` | Expedia EQC API secret |
| `MMT_API_KEY` | MakeMyTrip API key |
| `MMT_API_SECRET` | MakeMyTrip API secret |

## Notification Service

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kira:pass@postgres:5432/kira_notification` |
| `SECRET_KEY` | 32-character random string |
| `SMTP_HOST` | `smtp.sendgrid.net` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `apikey` |
| `SMTP_PASSWORD` | SendGrid API key |
| `EMAIL_FROM` | `noreply@kira.abodeab.com` |

## Admin Service

| Variable | Description |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://kira:pass@postgres:5432/kira_admin` |
| `SECRET_KEY` | 32-character random string |
| `SUPERADMIN_EMAIL` | Initial super-admin email |
| `SUPERADMIN_PASSWORD` | Initial super-admin password |
| `STRIPE_API_KEY` | Stripe secret key for billing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |

## Generating Secrets

```bash
# Generate a 32-character SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate a 64-character JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
