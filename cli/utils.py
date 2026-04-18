"""Shared CLI helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console

ROOT = Path(__file__).resolve().parent.parent
SERVICES = [
    "admin-service",
    "identity-service",
    "rate-inventory-service",
    "reservation-service",
    "channel-engine",
    "notification-service",
]

console = Console()
err_console = Console(stderr=True)


def info(msg: str) -> None:
    console.print(f"[bold cyan]→[/] {msg}")


def success(msg: str) -> None:
    console.print(f"[bold green]✔[/] {msg}")


def warn(msg: str) -> None:
    err_console.print(f"[bold yellow]⚠[/] {msg}")


def error(msg: str, *, abort: bool = True) -> None:
    err_console.print(f"[bold red]✖[/] {msg}")
    if abort:
        raise typer.Exit(code=1)


def _command_invokes_uv(cmd: list[str]) -> bool:
    if not cmd:
        return False
    return Path(cmd[0]).name == "uv"


def run(
    cmd: list[str],
    *,
    cwd: Path | str | None = None,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command, forwarding output by default."""
    import os

    merged_env = {**os.environ, **(env or {})}
    # When kira itself runs under `uv run kira`, VIRTUAL_ENV points at the root
    # kira-cli .venv. Nested `uv run …` in a service dir must pick that service's
    # project env; inherited VIRTUAL_ENV makes uv warn and ignore the wrong path.
    if _command_invokes_uv(cmd):
        merged_env.pop("VIRTUAL_ENV", None)
    try:
        return subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            check=check,
            text=True,
            capture_output=capture,
            env=merged_env,
        )
    except subprocess.CalledProcessError as exc:
        error(f"Command failed: {' '.join(cmd)} (exit {exc.returncode})")
        raise typer.Exit(code=exc.returncode)  # noqa: B904
    except FileNotFoundError:
        error(f"Command not found: {cmd[0]}")
        raise typer.Exit(code=127)  # noqa: B904


def require(*commands: str) -> None:
    """Abort if any required CLI tool is missing."""
    missing = [c for c in commands if shutil.which(c) is None]
    if missing:
        error(f"Missing required tools: {', '.join(missing)}")


def validate_service(name: str) -> str:
    """Validate a service name, returning it if valid."""
    if name not in SERVICES:
        error(f"Unknown service '{name}'. Valid: {', '.join(SERVICES)}")
    return name


def sync_poetry_service_env(svc_dir: Path) -> None:
    """Install Poetry-managed dependencies into the service ``.venv`` for ``uv run``.

    Services use ``[tool.poetry]`` without a full ``[project]`` table; ``uv run`` then
    relies on ``poetry.lock`` (or resolves on first ``poetry install``). Without this
    step, ``uv run alembic`` can fail with "Failed to spawn: alembic" because the venv
    has no application dependencies yet.
    """
    pyproject = svc_dir / "pyproject.toml"
    if not pyproject.is_file():
        return
    if "[tool.poetry]" not in pyproject.read_text():
        return
    run(
        [
            "uv",
            "run",
            "poetry",
            "install",
            "--no-root",
            "--no-interaction",
        ],
        cwd=svc_dir,
    )


def compose(*args: str, files: list[str] | None = None) -> list[str]:
    """Build a docker compose command list."""
    cmd = ["docker", "compose"]
    if files:
        for f in files:
            cmd.extend(["-f", f])
    else:
        cmd.extend(["-f", "docker/docker-compose.yml"])
    cmd.extend(args)
    return cmd
