"""kira lint — lint services and web app."""

from __future__ import annotations

import shutil
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
        if not _lint_shared(fix=fix):
            failed.append("shared")
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
    svc_dir = ROOT / "services" / name
    cmd = ["uv", "run", "ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.append(".")
    result = run(cmd, cwd=svc_dir, check=False)
    if result.returncode != 0:
        warn(f"  {name} has lint issues")
        return False
    fmt = (
        ["uv", "run", "ruff", "format", "."]
        if fix
        else ["uv", "run", "ruff", "format", "--check", "."]
    )
    result_fmt = run(fmt, cwd=svc_dir, check=False)
    if result_fmt.returncode != 0:
        warn(f"  {name} format check failed")
        return False
    success(f"  {name} clean")
    return True


def _lint_shared(*, fix: bool = False) -> bool:
    """Ruff for ``shared/`` using identity-service's venv (shared has no ruff dev dep)."""
    info("Linting shared (ruff via identity-service)…")
    anchor = ROOT / "services" / "identity-service"
    rel = "../../shared"
    chk = ["uv", "run", "ruff", "check"]
    if fix:
        chk.append("--fix")
    chk.append(rel)
    if run(chk, cwd=anchor, check=False).returncode != 0:
        warn("  shared has lint issues")
        return False
    fmt = (
        ["uv", "run", "ruff", "format", rel]
        if fix
        else ["uv", "run", "ruff", "format", "--check", rel]
    )
    if run(fmt, cwd=anchor, check=False).returncode != 0:
        warn("  shared format check failed")
        return False
    success("  shared clean")
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
    info("Linting web-app (tsc)…")
    tsc = (
        ["bunx", "tsc", "--noEmit"]
        if shutil.which("bun")
        else ["npx", "tsc", "--noEmit"]
    )
    if run(tsc, cwd=ROOT / "web-app", check=False).returncode != 0:
        warn("  web-app TypeScript check failed")
        return False
    success("  web-app clean")
    return True
