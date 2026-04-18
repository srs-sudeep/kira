"""kira test — run tests for services and web app."""

from __future__ import annotations

import os
from typing import Optional

import typer

from cli.utils import (
    ROOT,
    SERVICES,
    compose,
    error,
    info,
    run,
    success,
    validate_service,
    wait_for_postgres,
    warn,
)

app = typer.Typer(invoke_without_command=True)


def _skip_services() -> set[str]:
    """Read SKIP_TEST_SERVICES from env (space-separated service dir names)."""
    raw = os.environ.get("SKIP_TEST_SERVICES", "").strip()
    return set(raw.split()) if raw else set()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    service: Optional[str] = typer.Argument(None, help="Service name to test"),
    all: bool = typer.Option(False, "--all", help="Run tests for all services + web"),
    web: bool = typer.Option(False, "--web", help="Run web-app tests (Vitest)"),
    no_web: bool = typer.Option(
        False, "--no-web", help="When combined with --all, skip web-app tests"
    ),
    coverage: bool = typer.Option(
        False, "--coverage", help="Run with coverage (fail-under=70%)"
    ),
    integration: bool = typer.Option(
        False, "--integration", help="Run integration tests with infra"
    ),
) -> None:
    """Run tests for backend services and/or the web app."""
    if ctx.invoked_subcommand is not None:
        return

    if not any([service, all, web, coverage, integration]):
        info("Usage: kira test <service> | --all | --web | --coverage | --integration")
        raise typer.Exit()

    if integration:
        _run_integration()
        return

    skip = _skip_services()
    failed: list[str] = []

    if service:
        validate_service(service)
        if not _test_service(service, coverage=coverage):
            failed.append(service)

    if all:
        for svc in SERVICES:
            if svc in skip:
                info(f"Skipping {svc} (SKIP_TEST_SERVICES)")
                continue
            if not _test_service(svc, coverage=coverage):
                failed.append(svc)
        if not no_web:
            if not _test_web():
                failed.append("web-app")

    if web and not all:
        if not _test_web():
            failed.append("web-app")

    if failed:
        error(f"Tests failed for: {', '.join(failed)}")
    else:
        success("All tests passed")


def _test_service(name: str, *, coverage: bool = False) -> bool:
    info(f"Testing {name}…")
    cmd = ["uv", "run", "pytest", "-v"]
    if coverage:
        cmd.extend(["--cov", "--cov-report=html", "--cov-fail-under=70"])
    result = run(cmd, cwd=ROOT / "services" / name, check=False)
    if result.returncode != 0:
        warn(f"  {name} tests failed")
        return False
    success(f"  {name} passed")
    return True


def _test_web() -> bool:
    info("Testing web-app (Vitest)…")
    result = run(["bun", "run", "test"], cwd=ROOT / "web-app", check=False)
    if result.returncode != 0:
        warn("  web-app tests failed")
        return False
    success("  web-app passed")
    return True


def _run_integration() -> None:
    """Spin up infra, run integration-marked tests, tear down."""
    info("Starting infrastructure for integration tests…")
    run(compose("up", "-d", "postgres", "redis", "kafka"))

    wait_for_postgres(timeout_s=30)

    success("Infrastructure ready")

    skip = _skip_services()
    failed: list[str] = []
    try:
        for svc in SERVICES:
            if svc in skip:
                info(f"Skipping integration: {svc} (SKIP_TEST_SERVICES)")
                continue
            info(f"Integration testing {svc}…")
            result = run(
                ["uv", "run", "pytest", "-v", "-m", "integration"],
                cwd=ROOT / "services" / svc,
                check=False,
            )
            if result.returncode not in (0, 5):
                failed.append(svc)
            elif result.returncode == 5:
                warn(f"  {svc}: no tests matched -m integration (ok)")
    finally:
        info("Tearing down infrastructure…")
        run(compose("down", "postgres", "redis", "kafka"), check=False)

    if failed:
        error(f"Integration tests failed for: {', '.join(failed)}")
    else:
        success("All integration tests passed")
