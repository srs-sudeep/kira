"""kira migrate — database migrations via Alembic."""

from __future__ import annotations

from typing import Optional

import typer

from cli.utils import ROOT, SERVICES, compose, info, run, success, validate_service

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    service: Optional[str] = typer.Argument(None, help="Service to migrate"),
    all: bool = typer.Option(False, "--all", help="Migrate all services"),
    docker: bool = typer.Option(False, "--docker", help="Run inside Docker containers"),
) -> None:
    """Run Alembic migrations for one or all services."""
    if ctx.invoked_subcommand is not None:
        return

    if not service and not all:
        info("Usage: kira migrate <service> | --all [--docker]")
        raise typer.Exit()

    targets = SERVICES if all else [validate_service(service)]

    for svc in targets:
        info(f"Migrating {svc}{'  (Docker)' if docker else ''}…")
        if docker:
            run(
                compose(
                    "exec", svc, "sh", "-c", "cd /app && python -m alembic upgrade head"
                )
            )
        else:
            run(
                ["uv", "run", "alembic", "upgrade", "head"], cwd=ROOT / "services" / svc
            )
        success(f"  {svc} migrated")

    success("All migrations complete")
