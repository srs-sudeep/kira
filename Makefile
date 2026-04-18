.PHONY: up up-full down logs test-% test-all test-web test-coverage test-integration test-pre-push migrate-% migrate-all migrate-docker-% migrate-docker-all \
	seed seed-docker bootstrap wait-postgres clean dashboards dashboards-full stack-status docs-dev docs-build docs-docker-up dev-setup superadmin help

# ---------------------------------------------------------------------------
# Primary interface: kira CLI (uv run kira …). Makefile is a thin convenience
# layer for muscle memory, CI, and tools that only know `make`.
# ---------------------------------------------------------------------------

## Start core stack (infra + API services + Kong + web-app on :3000)
up:
	uv run kira dev up

## Start full stack with observability (Grafana, Prometheus, Loki, …)
up-full:
	uv run kira dev up --full

## Stop and remove containers (keep volumes)
down:
	uv run kira dev down

## Follow logs for all containers
logs:
	uv run kira dev logs

## Follow logs for a specific service — usage: make logs-identity-service
logs-%:
	uv run kira dev logs $*

## Show container status (use when /docs or dashboards fail to load)
stack-status:
	uv run kira dev status

# ---------------------------------------------------------------------------
# Testing — see cli/test.py
# ---------------------------------------------------------------------------

## Run tests for a specific service — usage: make test-identity-service
test-%:
	uv run kira test $*

## Run tests for all Python services (no web). Env: SKIP_TEST_SERVICES="svc …"
test-all:
	uv run kira test --all --no-web

## Run web-app tests (Vitest)
test-web:
	uv run kira test --web

## Run tests with coverage for all services (fail-under=70%)
test-coverage:
	uv run kira test --all --coverage --no-web

## Run integration tests (starts infra containers)
test-integration:
	uv run kira test --integration

## Run service pytest, web Vitest, then integration (Husky pre-push; sequential).
## Skip flags (export or prefix the command): SKIP_TEST_PRE_PUSH=1 skips the whole suite;
## SKIP_TEST_ALL=1, SKIP_TEST_WEB=1, SKIP_TEST_INTEGRATION=1 skip each stage;
## SKIP_TEST_SERVICES="svc …" skips those dirs in test-all and in integration.
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
# Migrations — see cli/migrate.py
# ---------------------------------------------------------------------------

## Run Alembic migrations for a specific service — usage: make migrate-identity-service
migrate-%:
	uv run kira migrate $*

## Run migrations for all services sequentially (host)
migrate-all:
	uv run kira migrate --all

## Run Alembic inside one container — usage: make migrate-docker-identity-service
migrate-docker-%:
	uv run kira migrate $* --docker

## Run all service migrations inside Docker (preferred after make up)
migrate-docker-all:
	uv run kira migrate --all --docker

# ---------------------------------------------------------------------------
# Data — see cli/seed.py
# ---------------------------------------------------------------------------

## Seed dev data from the host (Postgres must be reachable at localhost:5432)
seed:
	uv run kira seed

## Seed dev data via Docker Compose (Postgres up; run migrate-docker-all first)
seed-docker:
	uv run kira seed --docker

## Create a super-admin user (interactive; run on host)
superadmin:
	uv run kira seed superadmin

## First-time setup: start stack, wait for Postgres, migrate in Docker, seed in Docker
bootstrap:
	uv run kira dev bootstrap

## Wait until Postgres accepts connections
wait-postgres:
	uv run kira dev wait-postgres

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

## Stop everything and remove containers, volumes, and orphans
clean:
	uv run kira dev clean --yes

# ---------------------------------------------------------------------------
# Dashboards — see cli/__main__.py dashboards
# ---------------------------------------------------------------------------

## Core stack URLs (requires: make up)
dashboards:
	@uv run kira dashboards

## Observability + debug UIs (requires: make up-full)
dashboards-full:
	@uv run kira dashboards --full

# ---------------------------------------------------------------------------
# Documentation — see cli/docs.py
# ---------------------------------------------------------------------------

## Docusaurus dev server with hot reload (http://localhost:4000) — run on host
docs-dev:
	uv run kira docs dev

## Build static documentation site
docs-build:
	uv run kira docs build

## Serve built docs in Docker (http://localhost:4000) — rebuild image after doc changes
docs-docker-up:
	uv run kira docs docker-up

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
	@echo "Prefer the CLI (same behavior as these targets):"
	@echo "  uv run kira --help"
	@echo "  uv run kira dev --help"
	@echo ""
	@echo "First-time (Docker):"
	@echo "  make bootstrap       OR  uv run kira dev bootstrap"
	@echo ""
	@echo "Stack:"
	@echo "  make up              OR  uv run kira dev up"
	@echo "  make up-full         OR  uv run kira dev up --full"
	@echo "  make down            OR  uv run kira dev down"
	@echo "  make clean           OR  uv run kira dev clean --yes"
	@echo ""
	@echo "DB (stack running):"
	@echo "  make migrate-docker-all   OR  uv run kira migrate --all --docker"
	@echo "  make seed-docker          OR  uv run kira seed --docker"
	@echo ""
	@echo "DB (host, uv + localhost:5432):"
	@echo "  make migrate-all     OR  uv run kira migrate --all"
	@echo "  make seed            OR  uv run kira seed"
	@echo ""
	@echo "Logs:"
	@echo "  make logs            OR  uv run kira dev logs"
	@echo "  make logs-<service>  OR  uv run kira dev logs <service>"
	@echo ""
	@echo "Tests:"
	@echo "  make test-<service>  OR  uv run kira test <service>"
	@echo "  make test-all        OR  uv run kira test --all --no-web"
	@echo "  make test-web        OR  uv run kira test --web"
	@echo "  make test-coverage   OR  uv run kira test --all --coverage --no-web"
	@echo "  make test-integration  OR  uv run kira test --integration"
	@echo "  make test-pre-push   (orchestrator; skip envs documented in .husky/pre-push)"
	@echo ""
	@echo "Docs:"
	@echo "  make docs-dev        OR  uv run kira docs dev"
	@echo "  make docs-docker-up  OR  uv run kira docs docker-up"
	@echo ""
	@echo "  make dashboards      OR  uv run kira dashboards"
	@echo "  make dashboards-full OR  uv run kira dashboards --full"
	@echo "  make stack-status    OR  uv run kira dev status"
	@echo ""
