"""KIRA CLI — unified monorepo management tool.

Usage:
    uv run kira --help              # from repository root only
    ./bin/kira --help               # from anywhere in the clone
    uv tool install --editable .    # once from clone root → global `kira` on PATH
    uvx --from . kira --help        # ephemeral; run from clone root (--from path otherwise)

From a service directory, plain `uv run kira` binds to that folder's
pyproject.toml and cannot find this entry point. Prefer `./bin/kira`, a
global install via `uv tool install --editable .`, or
`uv run --project /path/to/Kira kira`.

Do not use bare `uvx kira`; that resolves a different PyPI project.
"""

from __future__ import annotations

import typer

from cli.deploy import app as deploy_app
from cli.dev import app as dev_app
from cli.docs import app as docs_app
from cli.lint import app as lint_app
from cli.migrate import app as migrate_app
from cli.push import register_push
from cli.seed import app as seed_app
from cli.test import app as test_app

app = typer.Typer(
    name="kira",
    help="KIRA — Hotel Channel Manager monorepo CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(dev_app, name="dev", help="Local development stack management")
app.add_typer(test_app, name="test", help="Run tests (services, web, integration)")
app.add_typer(migrate_app, name="migrate", help="Database migrations via Alembic")
app.add_typer(seed_app, name="seed", help="Seed development data")
app.add_typer(deploy_app, name="deploy", help="Deploy to staging / production")
app.add_typer(docs_app, name="docs", help="Documentation site management")
app.add_typer(lint_app, name="lint", help="Lint services and web app")

register_push(app)


@app.command()
def commit() -> None:
    """Open Commitizen interactive commit prompt."""
    from cli.utils import require, run

    require("npx")
    run(["npx", "cz"])


# Local dev URLs (see docs-site/docs/getting-started/dev-dashboards.md).
_DASHBOARD_CORE: list[str] = [
    "http://localhost:3000",  # web-app (Vite)
    "http://localhost:4000",  # docs-site (Docker profile docs or make docs-dev)
    "http://localhost:8025",  # Mailhog
    "http://localhost:8000",  # Kong proxy (gateway landing)
    "http://localhost:8100",  # Kong admin API (declarative / status)
]
# FastAPI OpenAPI — one tab per service (Kong does not proxy /docs).
_DASHBOARD_SERVICE_DOCS: list[str] = [
    "http://localhost:8001/docs",  # identity-service
    "http://localhost:8002/docs",  # rate-inventory-service
    "http://localhost:8003/docs",  # reservation-service
    "http://localhost:8004/docs",  # channel-engine
    "http://localhost:8005/docs",  # notification-service
    "http://localhost:8006/docs",  # admin-service
]
_DASHBOARD_OBSERVABILITY: list[str] = [
    "http://localhost:3001",  # Grafana
    "http://localhost:9090",  # Prometheus
    "http://localhost:3100",  # Loki (API; query via Grafana)
    "http://localhost:12345",  # Grafana Alloy
    "http://localhost:5050",  # pgAdmin
    "http://localhost:5540",  # Redis Insight
    "http://localhost:8080",  # Kafka UI
    "http://localhost:9000",  # Portainer (HTTP)
]


@app.command()
def dashboards(
    full: bool = typer.Option(
        False,
        "--full",
        "--all",
        help="Include observability UIs (Grafana, Prometheus, Loki, …)",
    ),
) -> None:
    """Open local dev URLs in the default browser (web :3000, docs :4000, Mailhog, Kong, each /docs, …)."""
    import webbrowser

    from cli.utils import info

    urls = [
        *_DASHBOARD_CORE,
        *_DASHBOARD_SERVICE_DOCS,
        *(_DASHBOARD_OBSERVABILITY if full else []),
    ]
    for url in urls:
        webbrowser.open(url)
    info(
        f"Opened {len(urls)} URL(s) — core + {len(_DASHBOARD_SERVICE_DOCS)} service /docs"
        + (f" + observability ({len(_DASHBOARD_OBSERVABILITY)})" if full else "")
    )


if __name__ == "__main__":
    app()
