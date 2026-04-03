---
title: Dev dashboards & ports
description: Ports for the web app, documentation site, observability UIs, and how sign-in works in local development.
sidebar_position: 3
---

# Dev dashboards, ports, and sign-in

Use this page as a quick reference for **local development** URLs. These settings are for convenience only — **do not** reuse default passwords in staging or production.

---

## Core ports (always use these)

| What | URL | Notes |
|------|-----|--------|
| **Web app (property manager UI)** | [http://localhost:3000](http://localhost:3000) | Vite dev server via Docker Compose (`web-app` service). API calls use `/api` → Kong. |
| **Documentation site (Docusaurus)** | [http://localhost:4000](http://localhost:4000) | **`make docs-dev`** (hot reload on the host), or **`make docs-docker-up`** (static build in Docker). Same port — run **one** at a time. |

The web client stays on **3000** and the docs site on **4000** by design so nothing clashes.

---

## Observability stack (`make up-full`)

After:

```bash
make up-full
```

these services are available (in addition to the core stack on 8000–8006 and 3000):

| Tool | URL | Sign-in / access |
|------|-----|------------------|
| **Grafana** | [http://localhost:3001](http://localhost:3001) | **Anonymous access enabled** — you land on the home page **without** typing a password (Viewer). To edit dashboards or settings, click **Sign in** and use **`admin` / `admin`**. |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | No authentication (local dev). |
| **Loki** | [http://localhost:3100](http://localhost:3100) | API only; use Grafana → Loki for log queries. |
| **Kafka UI** | [http://localhost:8080](http://localhost:8080) | **No login** — default app config uses `auth.type=DISABLED`. |
| **pgAdmin** | [http://localhost:5050](http://localhost:5050) | Log in with **`admin@kira.dev` / `admin`**. The **master password** prompt is disabled for local dev. The **KIRA Local** server is pre-registered; the DB password is supplied via a mounted `pgpass` file so you can connect without re-entering the Postgres password each time. |
| **Redis Insight** | [http://localhost:5540](http://localhost:5540) | Starts with **no connections** — Redis has no “database” list until you add one. Click **Add Redis database** → **Host:** `localhost` (from your Mac) or `redis` (from another container on `kira-net`) → **Port:** `6379` → **no password** (local dev). The key space is empty until the app writes keys. |
| **Portainer** | [https://localhost:9443](https://localhost:9443) | **Admin password is set on first init** from `observability/portainer/dev-admin-password` (default: **`KiraLocalPortainer!`**). If you already created an admin account in an older volume, this file is ignored — reset with `docker volume rm kira_portainerdata` (destructive) or use Portainer’s password recovery. |

:::warning Local development only
Grafana anonymous access, pgAdmin master-password bypass, and committed Portainer/pgAdmin passwords are **only** appropriate on your machine. Never enable these patterns for production.
:::

---

## Opening everything in the browser

- **Core stack** (after `make up`): `make dashboards`
- **Full observability** (after `make up-full`): `make dashboards-full`

`make dashboards` only works if the containers are **up and healthy**. Check with:

```bash
make stack-status
```

---

## Kong (`:8000`) vs OpenAPI (`:8001`–`:8006`)

| URL | What you get |
|-----|----------------|
| [http://localhost:8000/](http://localhost:8000/) | **Gateway landing page** — short HTML explaining that APIs live under `/api/v1/` and Swagger is on each service port. |
| [http://localhost:8000/api/v1/…](http://localhost:8000/api/v1/auth/login) | Proxied to the right microservice (e.g. auth). |
| `http://localhost:8000/docs` | **Not supported** — Kong does not proxy FastAPI’s `/docs`. Use **each service’s port** (e.g. [http://localhost:8001/docs](http://localhost:8001/docs)). |

---

## Troubleshooting: “connection reset” or blank pages

| Symptom | Likely cause | What to do |
|---------|----------------|------------|
| `ERR_CONNECTION_RESET` on `:8001/docs` … `:8006/docs` | The **service container is not running** (crash, failed build, or stack not started). | Run `make stack-status`. If a service is `Exited`, check `docker compose logs <service>`. Run `make up` or `make bootstrap`. |
| Grafana / pgAdmin / `:3001` won’t load | Observability stack not started. | Run **`make up-full`** (not only `make up`). Then use **`make dashboards-full`**, not `make dashboards`. |
| `:4000` won’t load | Docs site not running. | Run **`make docs-dev`** or **`make docs-docker-up`** on port 4000. |
| `:3000` blank | `web-app` container failed or still installing npm deps. | `docker compose logs web-app` — wait for Vite to print “ready”. |
| `Client sent an HTTP request to an HTTPS server` on `:9443` | Portainer only speaks **HTTPS** on that port. | Open **[https://localhost:9443](https://localhost:9443)** (note `https://`), not `http://`. |
| Kong `:8000` shows “no Route matched” | Stale Kong container or old `kong.yml` not mounted. | `docker compose restart kong` after `git pull`, or `make down && make up`. |

---

## Documentation site: two ways to run on :4000

| Command | What runs |
|---------|-----------|
| `make docs-dev` | Docusaurus **dev server** with hot reload (requires [bun](https://bun.sh) on the host). |
| `make docs-docker-up` | **Built** site served by nginx from the `docs-site` image (rebuild after changing markdown). |

Do not run both at the same time on port **4000**.

---

## Related

- [Local setup](./local-setup.md) — env files, `make bootstrap`, migrations, seed
- [Monitoring](../operations/monitoring.md) — Grafana/Prometheus in more detail
- [Deployment: local Docker](../deployment/local-docker.md) — compose files overview
