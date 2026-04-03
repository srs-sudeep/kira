.PHONY: up up-full down logs test-% test-all migrate-% migrate-all seed clean dashboards docs-dev docs-build

SERVICES := identity-service rate-inventory-service reservation-service channel-engine notification-service admin-service

# ---------------------------------------------------------------------------
# Stack management
# ---------------------------------------------------------------------------

## Start core stack (infra + services)
up:
	docker compose up -d --build

## Start full stack with observability dashboards
up-full:
	docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d --build

## Stop and remove containers (keep volumes)
down:
	docker compose -f docker-compose.yml -f docker-compose.observability.yml down

## Follow logs for all containers
logs:
	docker compose logs -f

## Follow logs for a specific service — usage: make logs-identity-service
logs-%:
	docker compose logs -f $*

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

## Run tests for a specific service — usage: make test-identity-service
test-%:
	cd services/$* && uv run pytest -v

## Run tests for all services sequentially
test-all:
	@for svc in $(SERVICES); do \
		echo "\n=== Testing $$svc ==="; \
		cd services/$$svc && uv run pytest -v; \
		cd ../..; \
	done

# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------

## Run Alembic migrations for a specific service — usage: make migrate-identity-service
migrate-%:
	cd services/$* && uv run alembic upgrade head

## Run migrations for all services sequentially
migrate-all:
	@for svc in $(SERVICES); do \
		echo "\n=== Migrating $$svc ==="; \
		cd services/$$svc && uv run alembic upgrade head; \
		cd ../..; \
	done

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

## Seed development data
seed:
	uv run python scripts/seed_data.py

## Create a super-admin user
superadmin:
	uv run python scripts/create_superadmin.py

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

## Stop everything and remove containers, volumes, and orphans
clean:
	docker compose -f docker-compose.yml -f docker-compose.observability.yml down -v --remove-orphans

# ---------------------------------------------------------------------------
# Dashboards — open all UIs in the default browser
# ---------------------------------------------------------------------------

## Open all service dashboards in the browser
dashboards:
	@echo "Opening KIRA dashboards..."
	@python3 -c "import webbrowser; urls = [ \
		'http://localhost:8025',   \
		'http://localhost:3001',   \
		'http://localhost:9090',   \
		'http://localhost:5050',   \
		'http://localhost:5540',   \
		'http://localhost:8080',   \
		'http://localhost:9443',   \
		'http://localhost:8000',   \
		'http://localhost:8001/docs',  \
		'http://localhost:8002/docs',  \
		'http://localhost:8003/docs',  \
		'http://localhost:8004/docs',  \
		'http://localhost:8005/docs',  \
		'http://localhost:8006/docs',  \
	]; [webbrowser.open(u) for u in urls]"

# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

## Start Docusaurus dev server (http://localhost:4000)
docs-dev:
	cd docs-site && bun install && bun run start -- --port 4000

## Build static documentation site
docs-build:
	cd docs-site && bun install && bun run build

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:
	@echo ""
	@echo "KIRA — Hotel Channel Manager"
	@echo "=============================="
	@echo ""
	@echo "Stack:"
	@echo "  make up              Start core stack"
	@echo "  make up-full         Start stack + observability"
	@echo "  make down            Stop containers"
	@echo "  make clean           Stop + remove volumes"
	@echo ""
	@echo "Logs:"
	@echo "  make logs            Tail all logs"
	@echo "  make logs-<service>  Tail a specific service"
	@echo ""
	@echo "Tests:"
	@echo "  make test-<service>  Run tests for one service"
	@echo "  make test-all        Run all service tests"
	@echo ""
	@echo "Migrations:"
	@echo "  make migrate-<svc>   Migrate one service"
	@echo "  make migrate-all     Migrate all services"
	@echo ""
	@echo "Data:"
	@echo "  make seed            Seed dev data"
	@echo "  make superadmin      Create super-admin user"
	@echo ""
	@echo "  make dashboards      Open all UIs in browser"
	@echo ""
	@echo "Docs:"
	@echo "  make docs-dev        Start Docusaurus dev server (port 4000)"
	@echo "  make docs-build      Build static docs site"
	@echo ""
