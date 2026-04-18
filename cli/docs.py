"""kira docs — documentation site management."""

from __future__ import annotations

import typer

from cli.utils import ROOT, info, run, success

app = typer.Typer(no_args_is_help=True)

DOCS_DIR = ROOT / "docs-site"


@app.command()
def dev() -> None:
    """Start Docusaurus dev server with hot reload (port 4000)."""
    info("Starting docs dev server on http://localhost:4000 …")
    run(["bun", "run", "start", "--", "--port", "4000"], cwd=DOCS_DIR)


@app.command()
def build() -> None:
    """Build the static documentation site."""
    info("Building documentation site…")
    run(["bun", "run", "build"], cwd=DOCS_DIR)
    success("Docs built → docs-site/build/")
