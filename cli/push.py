"""kira push — run pre-push tests then git push (optional interactive test selection)."""

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
        interactive: bool = typer.Option(
            False,
            "-i",
            "--interactive",
            help="Prompt for which test stages to run",
        ),
        skip_tests: bool = typer.Option(
            False,
            "--skip-tests",
            help="Skip tests in kira; git push sets SKIP_TEST_PRE_PUSH=1 so Husky does not re-run the suite",
        ),
        no_services: bool = typer.Option(
            False,
            "--no-services",
            help="Skip pytest in all Python services",
        ),
        no_web: bool = typer.Option(
            False,
            "--no-web",
            help="Skip web-app Vitest",
        ),
        no_integration: bool = typer.Option(
            False,
            "--no-integration",
            help="Skip Docker integration tests",
        ),
        skip_services: Optional[str] = typer.Option(
            None,
            "--skip-services",
            metavar="NAMES",
            help=f"Comma-separated services to skip in service tests + integration ({', '.join(SERVICES)})",
        ),
    ) -> None:
        """Run ``make test-pre-push`` (with optional skips), then ``git push``.

        Extra arguments are forwarded to ``git`` (for example ``kira push origin main`` or
        ``kira push -u origin my-branch``).

        After tests succeed here, ``git push`` runs with ``SKIP_TEST_PRE_PUSH=1`` so the Husky
        hook does not run the same suite again. Plain ``git push`` still runs the full hook.
        """
        require("git", "make")

        if interactive and (
            skip_tests or no_services or no_web or no_integration or skip_services
        ):
            error(
                "Use either --interactive or explicit skip flags / --skip-tests, not both."
            )

        git_args = list(ctx.args)

        test_env: dict[str, str] = {}
        if interactive:
            test_env = _interactive_test_env()
        elif skip_tests:
            test_env = {"SKIP_TEST_PRE_PUSH": "1"}
        else:
            if no_services:
                test_env["SKIP_TEST_ALL"] = "1"
            if no_web:
                test_env["SKIP_TEST_WEB"] = "1"
            if no_integration:
                test_env["SKIP_TEST_INTEGRATION"] = "1"
            if skip_services:
                test_env["SKIP_TEST_SERVICES"] = _comma_services_to_skip_env(
                    skip_services
                )

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
