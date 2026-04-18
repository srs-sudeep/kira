---
title: Local Setup
description: Clone the KIRA monorepo, configure environment variables, and start the full stack with Docker Compose.
sidebar_position: 2
---

# Local Setup

**What you'll learn:**

- How to clone the repo and configure per-service `.env.local` files
- What `docker compose up --build` actually does (which services start, in what order)
- How to run database migrations and seed test data
- How to confirm every service is healthy before opening the browser
- Common first-run problems and how to fix them

:::info Prerequisites
Complete the [Prerequisites](./prerequisites.md) guide before continuing. You need Docker Desktop (with 8 GB+ RAM allocated), Python 3.13, uv, and bun installed.
:::

---

## Quick Start (CLI)

The fastest way to get everything running:

```bash
git clone https://github.com/abodeab/kira.git
cd kira
uv run kira dev setup
```

This single command will:

1. Check all prerequisites are installed
2. Copy `.env.example` → `.env.local` for each service
3. Install npm dependencies (root + web-app)
4. Start infrastructure containers (Postgres, Redis, Kafka)
5. Run database migrations for all services
6. Seed development data

After setup completes, start the stack:

```bash
uv run kira dev up          # Start all services
uv run kira dashboards      # Open UIs in browser
```

See the [CLI Reference](./cli-reference.md) for the full command list.

:::tip Prefer the manual route?
The step-by-step instructions below do the same thing — use them if you want to understand each stage, or if you hit issues with the CLI setup.
:::

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/abodeab/kira.git
cd kira
```

---

## Step 2 — Configure Environment Variables

Each backend service reads its configuration from a `.env.local` file in its own directory. The repo ships `.env.example` files for each service — copy them:

```bash
# Copy .env.example → .env.local for each backend service
for svc in identity-service rate-inventory-service reservation-service \
           channel-engine notification-service admin-service; do
  cp services/$svc/.env.example services/$svc/.env.local
done
```

Then open each `.env.local` and fill in the values. For local development the defaults in `.env.example` work out of the box (they point to the Docker Compose service hostnames — `postgres`, `redis`, `kafka`).

:::warning Secret you must generate
`SECRET_KEY` in each service's `.env.local` is used for JWT signing and verification. For local development the shipped `.env.local` files include a dev-only value. For any shared or deployed environment, generate a unique key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the same value into **every** service's `.env.local` (all services must share the key to verify JWTs issued by identity-service).
:::

For the full list of variables and what each one does, see [Environment Variables](./environment-variables.md).

---

## Step 3 — Start the Stack

```bash
docker compose up -d --build
```

**What happens during this command:**

1. Docker pulls base images (only on first run — `postgres:16-alpine`, `redis:7-alpine`, `confluentinc/cp-kafka:7.5.0`, `kong:3.4-alpine`)
2. Docker builds all 7 application images in parallel (identity-service, rate-inventory-service, reservation-service, channel-engine, notification-service, admin-service, web-app)
3. Infrastructure containers start first: PostgreSQL, Redis, Zookeeper, Kafka
4. Health checks pass, then application services start
5. Celery workers start after their parent services
6. Kong gateway starts and loads the route config from `kong/kong.yml`
7. All containers reach `healthy` state

First build takes **3–6 minutes** depending on your internet speed and machine. Subsequent starts (without `--build`) take **under 30 seconds**.

:::tip Watching the build
Drop the `-d` flag to see live output:

```bash
docker compose up --build
```

Use `Ctrl+C` to detach once everything is up (or run in a separate terminal).
:::

---

## Step 4 — Run Database Migrations

Each service manages its own PostgreSQL schema with Alembic.

### Option A — Everything in Docker (recommended)

With the stack running (`make up`), apply migrations **inside** the containers so they use the `postgres` hostname from `.env.local`:

```bash
make migrate-docker-all
```

Single service: `make migrate-docker-identity-service` (replace with the service name).

### Option B — On your host (uv + localhost)

If Postgres is reachable at `localhost:5432`:

```bash
make migrate-all
```

This runs `alembic upgrade head` for each service in sequence. You should see output like:

```
=== Migrating identity-service ===
INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, initial schema

=== Migrating rate-inventory-service ===
INFO  [alembic.runtime.migration] Running upgrade  -> b2c3d4e5f6a1, initial schema
...
```

If you prefer to migrate one service at a time:

```bash
make migrate-identity-service
make migrate-rate-inventory-service
# ... etc
```

---

## Step 5 — Seed Test Data

**Docker (uses the Compose network to reach Postgres):**

```bash
make seed-docker
```

**Host (requires `uv`, same DSN as localhost:5432):**

```bash
make seed
```

**All-in-one** after a fresh clone: `make bootstrap` runs `up`, waits for Postgres, `migrate-docker-all`, and `make seed-docker`.

This runs `scripts/seed_data.py` which creates:

- A test tenant: **"Grand Hotel Demo"** (ID is printed to stdout — save it)
- A super-admin user: `admin@example.com` / `Admin1234!`
- One hotel admin user: `manager@grandhotel.example.com` / `Manager1234!`

:::caution Login emails and `.local`
Use addresses that pass API validation (e.g. `@example.com`, `@grandhotel.example.com`). The identity service uses Pydantic **`EmailStr`**, which **rejects** domains like **`*.local`** (reserved for mDNS). If you see `422` with “not a valid email address” for `@kira.local`, switch to the addresses above or run `make superadmin` with an allowed email.
:::

- Three room types: Standard Twin, Deluxe King, Suite
- Rate plans for each room type: BAR, Non-Refundable
- 30 days of ARI data starting from today

To also create a super-admin outside of seeding (e.g., to reset credentials):

```bash
make superadmin
```

### Re-run seed after credential / email changes

If you switched to `admin@example.com` / `manager@grandhotel.example.com` (or updated `scripts/seed_data.py`), apply it to the database:

- **Docker Compose Postgres** (stack running, migrations already applied):

  ```bash
  make seed-docker
  ```

- **Postgres on localhost:5432** (from repo root, with `uv`):

  ```bash
  make seed
  ```

The script **upserts** those two users by email, so passwords and roles refresh even if the rows already exist. It does not delete old accounts (e.g. `admin@kira.local`); remove those manually in Postgres if you no longer need them.

---

## Step 6 — Confirm Everything Is Healthy

```bash
docker compose ps
```

All containers should show `healthy` in the `STATUS` column. Then ping each service health endpoint:

```bash
curl -s http://localhost:8001/health | python3 -m json.tool
curl -s http://localhost:8002/health | python3 -m json.tool
curl -s http://localhost:8003/health | python3 -m json.tool
curl -s http://localhost:8004/health | python3 -m json.tool
curl -s http://localhost:8005/health | python3 -m json.tool
curl -s http://localhost:8006/health | python3 -m json.tool
```

Each should return:

```json
{
  "status": "ok",
  "service": "identity-service",
  "version": "1.0.0"
}
```

---

## Step 7 — Open the Dashboard

Navigate to [http://localhost:3000](http://localhost:3000) in your browser.

Log in with the seeded hotel admin:

- **Email:** `manager@grandhotel.example.com`
- **Password:** `Manager1234!`

You should land on the dashboard showing the KPI cards and the seeded reservation data.

To log in as super-admin (full platform access, including the admin-service):

- **Email:** `admin@example.com`
- **Password:** `Admin1234!`

---

## Optional — Observability dashboards

Add Grafana, Prometheus, Loki, Kafka UI, pgAdmin, etc.:

```bash
make up-full
```

Then open the observability URLs in your browser:

```bash
make dashboards-full
```

For the **core** stack only (web, Mailhog, Kong landing, one Swagger tab): `make dashboards` after `make up`. See [Dev dashboards & ports](./dev-dashboards.md) for what each command opens.

| Dashboard      | URL                                      | Purpose                                                                                  |
| -------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------- |
| KIRA web-app   | [localhost:3000](http://localhost:3000)  | Property manager dashboard                                                               |
| Kong proxy     | [localhost:8000](http://localhost:8000)  | API gateway (HTML landing on `/`; APIs under `/api/v1/`)                                 |
| Kong Admin API | [localhost:8100](http://localhost:8100)  | Kong admin (not Swagger)                                                                 |
| Grafana        | [localhost:3001](http://localhost:3001)  | Metrics + logs (anonymous or admin/admin)                                                |
| Prometheus     | [localhost:9090](http://localhost:9090)  | Raw metrics browser                                                                      |
| Kafka UI       | [localhost:8080](http://localhost:8080)  | Topic browser, consumer lag                                                              |
| pgAdmin        | [localhost:5050](http://localhost:5050)  | SQL browser — **`admin@kira.dev` / `admin`** (see [Dev dashboards](./dev-dashboards.md)) |
| Redis Insight  | [localhost:5540](http://localhost:5540)  | Redis key browser                                                                        |
| Mailhog        | [localhost:8025](http://localhost:8025)  | Outbound email trap                                                                      |
| Portainer      | [localhost:9443](https://localhost:9443) | Container management UI                                                                  |

---

## Stopping and Cleaning Up

```bash
# Stop all containers (data persists in Docker volumes)
make down

# Stop and delete all data (wipes PostgreSQL, Redis, Kafka)
make clean
```

:::danger `make clean` is destructive
`make clean` runs `docker compose down -v`, which deletes all named volumes including your PostgreSQL data. You will need to re-run migrations and seeding after this.
:::

---

## Troubleshooting

### Port already in use

```
Error: bind: address already in use — 0.0.0.0:5432
```

Another service on your machine is using that port. Find and stop it:

```bash
# Find what's using port 5432 (PostgreSQL)
lsof -i :5432

# Or kill it directly
sudo kill -9 $(lsof -t -i :5432)
```

Common culprits: a local PostgreSQL installation, another Docker Compose project. You can also change the host-side port in `docker-compose.yml` (e.g., `"5433:5432"`) without affecting anything else.

---

### Docker runs out of memory / services crash immediately

Symptom: Kafka or PostgreSQL containers exit with code 137 (OOM kill).

Fix: Open Docker Desktop → Settings → Resources → Memory → increase to at least **8 GB**, then restart Docker Desktop.

---

### PostgreSQL not ready / services fail to connect on first start

Symptom: A service exits with `could not connect to server: Connection refused`.

This usually means the service started before PostgreSQL finished its initialisation. The `depends_on: { condition: service_healthy }` config handles this, but occasionally the health check fires before Postgres is truly ready on the first ever run.

Fix:

```bash
docker compose down
docker compose up -d --build
```

The second start is always faster because the PostgreSQL data volume is already initialised.

---

### `make migrate-all` fails with "relation already exists"

This happens if you run migrations against a database that already has those tables (e.g., from a previous run). It is safe to ignore — Alembic only applies new migrations, and "already exists" means you are already up to date.

If you see actual errors (not warnings), run:

```bash
# Reset a specific service's schema and re-migrate
make migrate-identity-service
```

---

### Identity service starts but login returns 500

Make sure `SECRET_KEY` and `JWT_SECRET_KEY` are set in `services/identity-service/.env.local`. These cannot be empty — see Step 2 above.

---

## Next Step

→ **[First Run](./first-run.md)** — walkthrough of creating a test tenant, adding room types, making a reservation, and exploring the dashboard.
