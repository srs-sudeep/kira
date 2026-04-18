"""kira dev — local development stack management."""

from __future__ import annotations

import os
import shutil
import time
from typing import Optional

import typer

from cli.utils import (
    ROOT,
    SERVICES,
    compose,
    error,
    info,
    require,
    run,
    success,
    sync_poetry_service_env,
    warn,
)

app = typer.Typer(no_args_is_help=True)


def _run_dev_setup_core() -> None:
    """Bootstrap steps shared by ``setup`` and ``e2e`` (prereqs through seed)."""
    # 1 — Prerequisites
    info("Checking prerequisites…")
    require("docker", "uv", "bun")
    # Verify docker compose v2 plugin
    result = run(["docker", "compose", "version"], capture=True, check=False)
    if result.returncode != 0:
        error("docker compose v2 plugin not found")
    success("Prerequisites OK")

    # 2 — Copy .env.example → .env.local per service
    info("Setting up environment files…")
    for svc in SERVICES:
        example = ROOT / "services" / svc / ".env.example"
        local = ROOT / "services" / svc / ".env.local"
        if local.exists():
            warn(f"  {svc}/.env.local already exists — skipping")
        elif example.exists():
            shutil.copy2(example, local)
            success(f"  {svc}/.env.local created from .env.example")
        else:
            warn(f"  {svc}/.env.example not found — skipping")

    # 3 — bun install at root (Husky, Commitizen, Commitlint, lint-staged)
    if (ROOT / "package.json").exists():
        info("Installing root dependencies (Husky, Commitizen, Commitlint)…")
        run(["bun", "install"], cwd=ROOT)
        success("Root deps installed")

    # 4 — bun install in web-app
    info("Installing web-app dependencies…")
    run(["bun", "install"], cwd=ROOT / "web-app")
    success("web-app deps installed")

    # 5 — Start infra containers only
    info("Starting infrastructure containers (postgres, redis, kafka)…")
    run(compose("up", "-d", "postgres", "redis", "kafka"))
    success("Infrastructure containers started")

    # 6 — Wait for Postgres
    info("Waiting for Postgres to accept connections…")
    for i in range(30):
        result = run(
            compose(
                "exec", "-T", "postgres", "pg_isready", "-U", "postgres", "-d", "kira"
            ),
            check=False,
            capture=True,
        )
        if result.returncode == 0:
            break
        time.sleep(1)
    else:
        error("Postgres did not become ready in 30 seconds")
    success("Postgres is ready")

    # 7 — Run migrations
    info("Running database migrations…")
    for svc in SERVICES:
        svc_dir = ROOT / "services" / svc
        sync_poetry_service_env(svc_dir)
        run(
            ["uv", "run", "python", "-m", "alembic", "upgrade", "head"],
            cwd=svc_dir,
        )
        success(f"  {svc} migrated")

    # 8 — Seed data
    info("Seeding development data…")
    run(["uv", "run", "python", "scripts/seed_data.py"], cwd=ROOT)
    success("Development data seeded")


def _start_stack(*, full: bool) -> None:
    """Bring up Docker Compose (optionally with observability)."""
    if full:
        info("Starting full stack (core + observability + docs)…")
        run(
            compose(
                "--profile",
                "docs",
                "up",
                "-d",
                "--build",
                files=[
                    "docker/docker-compose.yml",
                    "docker/docker-compose.observability.yml",
                ],
            )
        )
    else:
        info("Starting core stack…")
        run(compose("up", "-d", "--build"))


@app.command()
def init(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Your developer name (used as DB suffix, e.g. 'alice' → kira_alice). "
        "Defaults to $USER.",
    ),
) -> None:
    """Set up per-developer database isolation.

    Creates docker/docker-compose.override.yml so each developer gets their own
    Postgres database (kira_<name>).  Run this once when you first clone
    the repo, or when you want to switch to a different personal DB.
    """
    dev_name = name or os.environ.get("USER", "dev")
    override = ROOT / "docker" / "docker-compose.override.yml"
    template = ROOT / "docker" / "docker-compose.override.yml.example"

    if override.exists():
        warn("docker/docker-compose.override.yml already exists")
        if not typer.confirm("Overwrite?"):
            raise typer.Abort()

    if not template.exists():
        error("docker/docker-compose.override.yml.example not found")

    info(f"Creating docker/docker-compose.override.yml  (DB: kira_{dev_name})")
    content = template.read_text().replace("${KIRA_DEV_USER:-dev}", dev_name)
    override.write_text(content)
    success(f"Override file written — database will be: kira_{dev_name}")
    info("Next steps:")
    info("  kira dev clean       # remove old volume if switching DBs")
    info("  kira dev up          # creates the new DB automatically")
    info("  kira migrate --all --docker")
    info("  kira seed --docker")


@app.command()
def setup() -> None:
    """Bootstrap the local development environment from scratch.

    Checks prerequisites, copies env files, installs dependencies,
    starts infrastructure containers, runs migrations, and seeds data.
    """
    from rich.panel import Panel

    from cli.utils import console

    console.print(Panel("KIRA Dev Setup", style="bold cyan"))
    _run_dev_setup_core()

    # 9 — Summary
    console.print()
    console.print(
        Panel.fit(
            "[bold green]Setup complete![/]\n\n"
            "Next steps:\n"
            "  [cyan]kira dev up[/]              Start all app services\n"
            "  [cyan]kira dev up --full[/]        Core + observability stack\n"
            "  [cyan]kira dev e2e[/]              Or: setup + up --full in one go\n"
            "  [cyan]cd web-app && bun run dev[/]  Frontend dev server\n"
            "  [cyan]kira dashboards[/]           Open UIs in browser\n"
            "  [cyan]kira dashboards --full[/]   Include observability UIs\n"
            "  [cyan]kira commit[/]              Conventional commit (Commitizen)",
            title="🎉 KIRA Ready",
        )
    )


@app.command("e2e")
def e2e() -> None:
    """End-to-end: run ``setup`` (infra, migrate, seed) then ``up --full``."""
    from rich.panel import Panel

    from cli.utils import console

    console.print(
        Panel(
            "KIRA Dev E2E — setup + full stack (core + observability)",
            style="bold cyan",
        )
    )
    _run_dev_setup_core()
    _start_stack(full=True)
    console.print()
    console.print(
        Panel.fit(
            "[bold green]E2E complete![/]\n\n"
            "Next steps:\n"
            "  [cyan]cd web-app && bun run dev[/]  Frontend dev server\n"
            "  [cyan]kira dashboards --full[/]     Open core + observability UIs\n"
            "  [cyan]kira dev status[/]           Container health\n"
            "  [cyan]kira commit[/]              Conventional commit",
            title="🎉 Stack is up",
        )
    )
    success("E2E complete")


@app.command()
def up(
    full: bool = typer.Option(False, "--full", help="Include observability stack"),
) -> None:
    """Start the Docker Compose stack."""
    _start_stack(full=full)
    success("Stack is up")


@app.command()
def down() -> None:
    """Stop and remove containers (keep volumes)."""
    info("Stopping stack…")
    run(
        compose(
            "down",
            files=[
                "docker/docker-compose.yml",
                "docker/docker-compose.observability.yml",
            ],
        )
    )
    success("Stack stopped")


@app.command()
def logs(
    service: Optional[str] = typer.Argument(
        None, help="Service name to tail (omit for all)"
    ),
) -> None:
    """Follow container logs."""
    if service:
        run(compose("logs", "-f", service))
    else:
        run(compose("logs", "-f"))


@app.command()
def status() -> None:
    """Show container status."""
    run(compose("ps", "-a"))


@app.command()
def clean() -> None:
    """Stop everything and remove containers, volumes, and orphans."""
    warn("This will remove all containers and volumes!")
    confirm = typer.confirm("Continue?")
    if not confirm:
        raise typer.Abort()
    run(
        compose(
            "down",
            "-v",
            "--remove-orphans",
            files=[
                "docker/docker-compose.yml",
                "docker/docker-compose.observability.yml",
            ],
        )
    )
    success("Cleaned up")
