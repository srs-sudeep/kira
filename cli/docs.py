"""kira docs — documentation site management."""

from __future__ import annotations

import typer

from cli.utils import ROOT, compose, info, require, run, success

app = typer.Typer(no_args_is_help=True)

DOCS_DIR = ROOT / "docs-site"


@app.command()
def dev() -> None:
    """Start Docusaurus dev server with hot reload (port 4000)."""
    require("bun")
    info("Installing docs-site dependencies…")
    run(["bun", "install"], cwd=DOCS_DIR)
    info("Starting docs dev server on http://localhost:4000 …")
    run(["bun", "run", "start"], cwd=DOCS_DIR)


@app.command()
def build() -> None:
    """Build the static documentation site."""
    require("bun")
    info("Installing docs-site dependencies…")
    run(["bun", "install"], cwd=DOCS_DIR)
    info("Building documentation site…")
    run(["bun", "run", "build"], cwd=DOCS_DIR)
    success("Docs built → docs-site/build/")


@app.command("docker-up")
def docker_up() -> None:
    """Build and run the docs-site container (compose profile ``docs``)."""
    info("Starting docs-site in Docker on http://localhost:4000 …")
    run(compose("--profile", "docs", "up", "-d", "--build", "docs-site"))
    success("docs-site container is up")
