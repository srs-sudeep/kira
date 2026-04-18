"""kira lint — lint services and web app."""

from __future__ import annotations

from typing import Optional

import typer

from cli.utils import ROOT, SERVICES, error, info, run, success, validate_service, warn

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    service: Optional[str] = typer.Argument(None, help="Service to lint"),
    web: bool = typer.Option(False, "--web", help="Lint web-app only"),
    all: bool = typer.Option(False, "--all", help="Lint all services + web"),
    fix: bool = typer.Option(False, "--fix", help="Auto-fix where possible"),
) -> None:
    """Lint backend services (ruff) and/or web-app (eslint)."""
    if ctx.invoked_subcommand is not None:
        return

    if not any([service, web, all]):
        info("Usage: kira lint <service> | --web | --all [--fix]")
        raise typer.Exit()

    failed: list[str] = []

    if service:
        validate_service(service)
        if not _lint_service(service, fix=fix):
            failed.append(service)

    if all:
        for svc in SERVICES:
            if not _lint_service(svc, fix=fix):
                failed.append(svc)
        if not _lint_web(fix=fix):
            failed.append("web-app")

    if web and not all:
        if not _lint_web(fix=fix):
            failed.append("web-app")

    if failed:
        error(f"Lint failed for: {', '.join(failed)}")
    elif any([service, web, all]):
        success("All lint checks passed")


def _lint_service(name: str, *, fix: bool = False) -> bool:
    info(f"Linting {name} (ruff)…")
    cmd = ["uv", "run", "ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.append(".")
    result = run(cmd, cwd=ROOT / "services" / name, check=False)
    if result.returncode != 0:
        warn(f"  {name} has lint issues")
        return False
    success(f"  {name} clean")
    return True


def _lint_web(*, fix: bool = False) -> bool:
    info("Linting web-app (eslint)…")
    cmd = ["npx", "eslint", "."]
    if fix:
        cmd.append("--fix")
    result = run(cmd, cwd=ROOT / "web-app", check=False)
    if result.returncode != 0:
        warn("  web-app has lint issues")
        return False
    success("  web-app clean")
    return True
