"""kira seed — seed development data."""

from __future__ import annotations

import typer

from cli.utils import ROOT, compose, info, run, success

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    docker: bool = typer.Option(
        False, "--docker", help="Seed via Docker Compose profile"
    ),
) -> None:
    """Seed the database with development data."""
    if ctx.invoked_subcommand is not None:
        return

    if docker:
        info("Seeding via Docker Compose…")
        run(compose("--profile", "tools", "run", "--rm", "seed-data"))
    else:
        info("Seeding from host…")
        run(["uv", "run", "python", "scripts/seed_data.py"], cwd=ROOT)
    success("Development data seeded")


@app.command()
def superadmin() -> None:
    """Create a super-admin user interactively."""
    info("Creating super-admin user…")
    run(["uv", "run", "python", "scripts/create_superadmin.py"], cwd=ROOT)
