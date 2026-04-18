---
sidebar_position: 8
---

# Per-Developer Database Isolation

When multiple developers work on KIRA simultaneously, each person needs their own Postgres database to avoid schema conflicts, migration collisions, and stale test data.

## How It Works

Docker Compose supports an **override file** (`docker/docker-compose.override.yml`) that is automatically merged with the base `docker/docker-compose.yml`. Each developer creates their own override that sets a unique `POSTGRES_DB` name and updates `DATABASE_URL` for all services.

```
docker/docker-compose.yml                  ← shared, committed
docker/docker-compose.override.yml         ← per-developer, gitignored
docker/docker-compose.override.yml.example ← template, committed
```

## Quick Setup

```bash
# One-time: generate your personal override file
uv run kira dev init --name alice    # → DB: kira_alice

# Or accept the default ($USER):
uv run kira dev init                 # → DB: kira_<your-username>
```

This creates `docker/docker-compose.override.yml` from the committed template.

## What Changes

The override file sets these env vars for every service:

| Variable       | Base value              | Override value                |
| -------------- | ----------------------- | ----------------------------- |
| `POSTGRES_DB`  | `kira`                  | `kira_alice`                  |
| `DATABASE_URL` | `...postgres:5432/kira` | `...postgres:5432/kira_alice` |

All services, workers, and the postgres container are updated.

## First-Time Workflow

```bash
# 1. Clone and set up
git clone https://github.com/abodeab/kira.git && cd kira

# 2. Generate your personal DB override
uv run kira dev init --name alice

# 3. Start the stack (creates kira_alice DB automatically)
uv run kira dev up

# 4. Run migrations
uv run kira migrate --all --docker

# 5. Seed dev data
uv run kira seed --docker
```

## Switching Databases

If you need a fresh database or want to switch names:

```bash
# Remove the old DB volume
uv run kira dev clean

# Regenerate with a new name
uv run kira dev init --name alice-v2

# Restart + migrate + seed
uv run kira dev up
uv run kira migrate --all --docker
uv run kira seed --docker
```

## Running Services Outside Docker

If you run a service on the host (e.g., for debugging), update that service's `.env.local`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kira_alice
```

The Postgres container's port 5432 is mapped to the host, so both Docker-based and host-based services connect to the same DB.

## FAQ

**Q: What if I don't create an override file?**
The base `docker/docker-compose.yml` uses `POSTGRES_DB: kira`. Everything works, but you share the default DB name with anyone else who skips this step.

**Q: Can two developers use the same Postgres container?**
Yes — Postgres supports multiple databases in one server. Each developer's override creates a different database name within the same `postgres` container. There's no need for separate containers.

**Q: Do migrations need to run per-database?**
Yes. Each personal database starts empty. After `kira dev init` + `kira dev up`, you must run `kira migrate --all --docker` to apply schemas to your new database.
