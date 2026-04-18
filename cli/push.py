"""kira push — run pre-push tests then git push (interactive by default)."""

from __future__ import annotations

import os
from typing import Optional

import typer

from cli.utils import (
    ROOT,
    SERVICES,
    error,
    info,
    require,
    run,
    success,
    validate_service,
)


def _comma_services_to_skip_env(raw: str) -> str:
    """Makefile / scripts expect space-separated service dir names."""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    for p in parts:
        validate_service(p)
    return " ".join(parts)


def _interactive_test_env() -> dict[str, str]:
    """Prompt for which pre-push stages to run; returns env for ``make test-pre-push``."""
    env: dict[str, str] = {}
    info("Select which tests to run before push (defaults: all on)")
    if not typer.confirm("Run pytest in all Python services?", default=True):
        env["SKIP_TEST_ALL"] = "1"
    if not typer.confirm("Run web-app tests (Vitest)?", default=True):
        env["SKIP_TEST_WEB"] = "1"
    if not typer.confirm(
        "Run Docker integration tests (postgres/redis/kafka)?", default=True
    ):
        env["SKIP_TEST_INTEGRATION"] = "1"
    if env.get("SKIP_TEST_ALL") != "1":
        skip_raw = typer.prompt(
            "Comma-separated services to skip (empty for none)",
            default="",
            show_default=False,
        ).strip()
        if skip_raw:
            env["SKIP_TEST_SERVICES"] = _comma_services_to_skip_env(skip_raw)
    if (
        env.get("SKIP_TEST_ALL") == "1"
        and env.get("SKIP_TEST_WEB") == "1"
        and env.get("SKIP_TEST_INTEGRATION") == "1"
    ):
        if not typer.confirm(
            "No tests selected. Push without running tests?", default=False
        ):
            raise typer.Abort()
        return {"SKIP_TEST_PRE_PUSH": "1"}
    return env


def register_push(app: typer.Typer) -> None:
    """Attach ``kira push`` to the root CLI."""

    @app.command(
        "push",
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )
    def push_cmd(
        ctx: typer.Context,
        yes: bool = typer.Option(
            False,
            "-y",
            "--yes",
            help="Non-interactive: run the full pre-push suite (no prompts)",
        ),
        skip_tests: bool = typer.Option(
            False,
            "--skip-tests",
            help="Skip tests in kira; git push sets SKIP_TEST_PRE_PUSH=1 so Husky does not re-run the suite",
        ),
        no_services: bool = typer.Option(
            False,
            "--no-services",
            help="Skip pytest in all Python services (non-interactive)",
        ),
        no_web: bool = typer.Option(
            False,
            "--no-web",
            help="Skip web-app Vitest (non-interactive)",
        ),
        no_integration: bool = typer.Option(
            False,
            "--no-integration",
            help="Skip Docker integration tests (non-interactive)",
        ),
        skip_services: Optional[str] = typer.Option(
            None,
            "--skip-services",
            metavar="NAMES",
            help=f"Comma-separated services to skip (non-interactive; {', '.join(SERVICES)})",
        ),
    ) -> None:
        """Run ``make test-pre-push`` (with optional skips), then ``git push``.

        By default this command is **interactive**: you choose which test stages to run.

        Use **-y** / **--yes** for a non-interactive full suite (CI / scripts). Use **--skip-tests**,
        **--no-web**, etc. for non-interactive partial runs.

        Extra arguments are forwarded to ``git`` (for example ``kira push origin main``).

        After tests succeed here, ``git push`` runs with ``SKIP_TEST_PRE_PUSH=1`` so the Husky
        hook does not run the same suite again. Plain ``git push`` still runs the full hook.
        """
        require("git", "make")

        explicit_skips = any(
            [no_services, no_web, no_integration, skip_services is not None]
        )
        if skip_tests and (yes or explicit_skips):
            error("Do not combine --skip-tests with -y or other skip flags.")

        git_args = list(ctx.args)

        flag_env: dict[str, str] = {}
        if no_services:
            flag_env["SKIP_TEST_ALL"] = "1"
        if no_web:
            flag_env["SKIP_TEST_WEB"] = "1"
        if no_integration:
            flag_env["SKIP_TEST_INTEGRATION"] = "1"
        if skip_services:
            flag_env["SKIP_TEST_SERVICES"] = _comma_services_to_skip_env(skip_services)

        test_env: dict[str, str]
        if skip_tests:
            test_env = {"SKIP_TEST_PRE_PUSH": "1"}
        elif explicit_skips:
            test_env = flag_env
        elif yes:
            test_env = {}
        else:
            test_env = _interactive_test_env()

        run_make = not skip_tests and test_env.get("SKIP_TEST_PRE_PUSH") != "1"
        if run_make:
            info("Running make test-pre-push…")
            merged = {**os.environ, **test_env}
            result = run(["make", "test-pre-push"], cwd=ROOT, env=merged, check=False)
            if result.returncode != 0:
                error("Tests failed; fix or adjust skips before pushing.")
            success("Pre-push tests passed.")

        push_env = {**os.environ, "SKIP_TEST_PRE_PUSH": "1"}
        cmd = ["git", "push", *git_args]
        info(f"Running: {' '.join(cmd)}")
        run(cmd, cwd=ROOT, env=push_env)
