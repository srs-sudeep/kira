.PHONY: up up-full down logs test-% test-all test-web test-coverage test-integration test-pre-push migrate-% migrate-all migrate-docker-% migrate-docker-all \
	seed seed-docker bootstrap wait-postgres clean dashboards dashboards-full stack-status docs-dev docs-build docs-docker-up dev-setup help


SERVICES := admin-service identity-service rate-inventory-service reservation-service channel-engine notification-service

ROOT := $(abspath .)
COMPOSE := docker compose -f $(ROOT)/docker/docker-compose.yml
COMPOSE_FULL := docker compose -f $(ROOT)/docker/docker-compose.yml -f $(ROOT)/docker/docker-compose.observability.yml

# ---------------------------------------------------------------------------
# Stack management
# ---------------------------------------------------------------------------

## Start core stack (infra + API services + Kong + web-app on :3000)
up:
	$(COMPOSE) up -d --build

## Start full stack with observability (Grafana, Prometheus, Loki, …)
up-full:
	$(COMPOSE_FULL) up -d --build

## Stop and remove containers (keep volumes)
down:
	$(COMPOSE_FULL) down

## Follow logs for all containers
logs:
	$(COMPOSE) logs -f

## Follow logs for a specific service — usage: make logs-identity-service
logs-%:
	$(COMPOSE) logs -f $*

## Show container status (use when /docs or dashboards fail to load)
stack-status:
	$(COMPOSE) ps -a

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

## Run tests for a specific service — usage: make test-identity-service
test-%:
	cd services/$* && uv run pytest -v

## Run tests for all services sequentially. Optional: SKIP_TEST_SERVICES="identity-service admin-service"
test-all:
	@for svc in $(SERVICES); do \
		skip=0; for s in $(SKIP_TEST_SERVICES); do \
			if [ "$$s" = "$$svc" ]; then skip=1; break; fi; \
		done; \
		if [ "$$skip" -eq 1 ]; then echo "\n=== Skipping $$svc (SKIP_TEST_SERVICES) ==="; continue; fi; \
		echo "\n=== Testing $$svc ==="; \
		cd services/$$svc && uv run pytest -v; \
		cd ../..; \
	done

## Run web-app tests (Vitest)
test-web:
	cd web-app && bun run test

## Run tests with coverage for all services (fail-under=70%)
test-coverage:
	@for svc in $(SERVICES); do \
		echo "\n=== Coverage: $$svc ==="; \
		cd services/$$svc && uv run pytest --cov --cov-report=html --cov-fail-under=70 -v; \
		cd ../..; \
	done

## Run integration tests (starts infra containers)
test-integration:
	bash scripts/test_integration.sh

## Run service pytest, web Vitest, then integration (Husky pre-push; sequential).
## Skip flags (export or prefix the command): SKIP_TEST_PRE_PUSH=1 skips the whole suite;
## SKIP_TEST_ALL=1, SKIP_TEST_WEB=1, SKIP_TEST_INTEGRATION=1 skip each stage;
## SKIP_TEST_SERVICES="svc …" skips those dirs in test-all and in scripts/test_integration.sh.
## (One shell so SKIP_TEST_PRE_PUSH=1 exit applies to the whole target — not one line per subshell.)
test-pre-push:
	@set -e; \
	if [ "$$SKIP_TEST_PRE_PUSH" = "1" ]; then \
		echo "SKIP_TEST_PRE_PUSH=1 — skipping entire pre-push test suite"; \
		exit 0; \
	fi; \
	if [ "$$SKIP_TEST_ALL" != "1" ]; then $(MAKE) test-all; else echo "Skipping test-all (SKIP_TEST_ALL=1)"; fi; \
	if [ "$$SKIP_TEST_WEB" != "1" ]; then $(MAKE) test-web; else echo "Skipping test-web (SKIP_TEST_WEB=1)"; fi; \
	if [ "$$SKIP_TEST_INTEGRATION" != "1" ]; then $(MAKE) test-integration; else echo "Skipping test-integration (SKIP_TEST_INTEGRATION=1)"; fi

# ---------------------------------------------------------------------------
# Migrations (host — requires uv; uses localhost:5432)
# ---------------------------------------------------------------------------

## Run Alembic migrations for a specific service — usage: make migrate-identity-service
migrate-%:
	cd services/$* && uv run poetry install --no-root --no-interaction && uv run python -m alembic upgrade head

## Run migrations for all services sequentially (host)
migrate-all:
	@for svc in $(SERVICES); do \
		echo "\n=== Migrating $$svc ==="; \
		cd services/$$svc && uv run poetry install --no-root --no-interaction && uv run python -m alembic upgrade head; \
		cd ../..; \
	done

# ---------------------------------------------------------------------------
# Migrations (Docker — run inside each service container; uses postgres hostname)
# Requires: make up (stack running)
# ---------------------------------------------------------------------------

## Run Alembic inside one container — usage: make migrate-docker-identity-service
migrate-docker-%:
	$(COMPOSE) exec $* sh -c "cd /app && python -m alembic upgrade head"

## Run all service migrations inside Docker (preferred after make up)
migrate-docker-all:
	@for svc in $(SERVICES); do \
		echo "\n=== Migrating $$svc (Docker) ==="; \
		$(COMPOSE) exec $$svc sh -c "cd /app && python -m alembic upgrade head" || exit 1; \
	done

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

## Seed dev data from the host (Postgres must be reachable at localhost:5432)
## Set ENCRYPTION_KEY to match reservation-service / channel-engine .env.local (64-char hex).
seed:
	uv run python scripts/seed_data.py

## Seed dev data via Docker Compose (Postgres up; run migrate-docker-all first)
seed-docker:
	$(COMPOSE) --profile tools run --rm seed-data

## First-time setup: start stack, wait for Postgres, migrate in Docker, seed in Docker
bootstrap: up-full wait-postgres migrate-docker-all seed-docker
	@echo ""
	@echo "Done. Web UI: http://localhost:3000  |  Kong: http://localhost:8000"
	@echo "OpenAPI is on each service port (e.g. http://localhost:8001/docs), not on Kong."

## Wait until Postgres accepts connections
wait-postgres:
	@echo "Waiting for Postgres..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do \
		$(COMPOSE) exec -T postgres pg_isready -U postgres -d kira >/dev/null 2>&1 && exit 0; \
		sleep 1; \
	done; \
	echo "Postgres did not become ready in time."; exit 1

## Create a super-admin user (interactive; run on host)
superadmin:
	uv run python scripts/create_superadmin.py

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

## Stop everything and remove containers, volumes, and orphans
clean:
	$(COMPOSE_FULL) down -v --remove-orphans

# ---------------------------------------------------------------------------
# Dashboards — open UIs in the default browser (macOS/Linux)
# ---------------------------------------------------------------------------

## Core stack URLs (requires: make up — containers must be healthy)
dashboards:
	@echo "Opening KIRA core UIs (same as  uv run kira dashboards )…"
	@echo "Tip: Grafana/pgAdmin/Kafka UI need  make up-full  then  make dashboards-full"
	@echo "If tabs fail:  make stack-status   and   docker compose logs <service>"
	@uv run kira dashboards

## Observability + debug UIs (requires: make up-full — not started by make up alone)
dashboards-full:
	@echo "Opening KIRA + observability UIs (same as  uv run kira dashboards --full )…"
	@echo "If ports refuse connection, run:  make up-full"
	@uv run kira dashboards --full

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

## Docusaurus dev server with hot reload (http://localhost:4000) — run on host
docs-dev:
	cd docs-site && bun install && bun run start

## Build static documentation site
docs-build:
	cd docs-site && bun install && bun run build

## Serve built docs in Docker (http://localhost:4000) — rebuild image after doc changes
docs-docker-up:
	$(COMPOSE) --profile docs up -d --build docs-site

# ---------------------------------------------------------------------------
# Dev Setup
# ---------------------------------------------------------------------------

## Bootstrap local development environment via the kira CLI
dev-setup:
	uv run kira dev setup

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help:
	@echo ""
	@echo "KIRA — Hotel Channel Manager"
	@echo "=============================="
	@echo ""
	@echo "First-time (Docker):"
	@echo "  make bootstrap       Start stack, migrate DB in containers, seed data"
	@echo ""
	@echo "Stack:"
	@echo "  make up              Core: Postgres, Redis, Kafka, APIs, Kong, web :3000"
	@echo "  make up-full         Core + Grafana, Prometheus, Loki, …"
	@echo "  make down            Stop containers"
	@echo "  make clean           Stop + remove volumes"
	@echo ""
	@echo "DB (stack running):"
	@echo "  make migrate-docker-all   Alembic inside each service container"
	@echo "  make seed-docker        Seed script via Docker network"
	@echo ""
	@echo "DB (host, uv + localhost:5432):"
	@echo "  make migrate-all     Alembic on host for all services"
	@echo "  make seed            Seed script on host"
	@echo ""
	@echo "Logs:"
	@echo "  make logs            Tail all logs"
	@echo "  make logs-<service>  Tail one service"
	@echo ""
	@echo "Tests:"
	@echo "  make test-<service>  Run tests for one service"
	@echo "  make test-all        Run all service tests"
	@echo "  make test-web        Run web-app tests (Vitest)"
	@echo "  make test-coverage   Run tests with coverage"
	@echo "  make test-integration Run integration tests with infra"
	@echo "  make test-pre-push   test-all + test-web + test-integration (pre-push; see skip envs in Makefile)"
	@echo ""
	@echo "CLI:"
	@echo "  make dev-setup       Bootstrap local dev (via kira CLI)"
	@echo ""
	@echo "Docs:"
	@echo "  make docs-dev        Docusaurus dev server (host, port 4000)"
	@echo "  make docs-docker-up  Built docs in Docker (port 4000)"
	@echo ""
	@echo "  make dashboards      Open core UIs (kira dashboards: web, docs, Mailhog, Kong, all /docs)"
	@echo "  make dashboards-full After make up-full — same + Grafana, Prometheus, Loki, …"
	@echo "  make stack-status    docker compose ps (debug connection errors)"
	@echo ""
