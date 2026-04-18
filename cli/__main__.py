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


@app.command()
def commit() -> None:
    """Open Commitizen interactive commit prompt."""
    from cli.utils import require, run

    require("npx")
    run(["npx", "cz"])


@app.command()
def dashboards(
    full: bool = typer.Option(False, "--full", help="Include observability UIs"),
) -> None:
    """Open KIRA dashboard URLs in the default browser."""
    import webbrowser

    from cli.utils import info

    core = [
        "http://localhost:3000",
        "http://localhost:8025",
        "http://localhost:8000",
        "http://localhost:8001/docs",
    ]
    obs = [
        "http://localhost:3001",
        "http://localhost:9090",
        "http://localhost:5050",
        "http://localhost:5540",
        "http://localhost:8080",
        "http://localhost:12345",
        "http://localhost:9000",
    ]
    urls = core + obs if full else core
    for url in urls:
        webbrowser.open(url)
    info(f"Opened {len(urls)} dashboard(s) in your browser")


if __name__ == "__main__":
    app()
