"""kira deploy — deploy to staging / production."""

from __future__ import annotations

from typing import Optional

import typer

from cli.utils import ROOT, SERVICES, error, info, require, run, success, warn

app = typer.Typer(no_args_is_help=True)

ALL_IMAGES = SERVICES + ["web-app"]


def _get_git_sha() -> str:
    result = run(["git", "rev-parse", "--short", "HEAD"], capture=True)
    return result.stdout.strip()


def _get_ecr_registry() -> str:
    result = run(
        ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"],
        capture=True,
    )
    account_id = result.stdout.strip()
    result = run(
        ["aws", "configure", "get", "region"],
        capture=True,
        check=False,
    )
    region = result.stdout.strip() or "ap-south-1"
    return f"{account_id}.dkr.ecr.{region}.amazonaws.com"


def _deploy(
    env: str,
    *,
    overlay: str,
    namespace: str,
    skip_terraform: bool,
    services: Optional[str],
    dry_run: bool,
) -> None:
    """Shared deploy logic for staging/production."""
    require("aws", "docker", "kubectl")

    sha = _get_git_sha()
    info(f"Deploying to [bold]{env}[/] (commit {sha})")

    # Validate AWS credentials
    info("Validating AWS credentials…")
    run(["aws", "sts", "get-caller-identity"], capture=True)
    success("AWS credentials valid")

    registry = _get_ecr_registry()

    # Terraform
    if not skip_terraform:
        require("terraform")
        tf_dir = ROOT / "infra" / "terraform"
        info("Running Terraform…")

        if dry_run:
            info("[dim](dry-run) Would run: terraform init + plan + apply[/]")
        else:
            run(["terraform", "init"], cwd=tf_dir)
            run(["terraform", "plan", "-out=tfplan"], cwd=tf_dir)
            if not typer.confirm("Apply Terraform changes?"):
                raise typer.Abort()
            run(["terraform", "apply", "tfplan"], cwd=tf_dir)
            success("Terraform applied")

    # Determine which images to build
    targets = ALL_IMAGES
    if services:
        targets = [s.strip() for s in services.split(",")]
        for t in targets:
            if t not in ALL_IMAGES:
                error(f"Unknown service/image: {t}. Valid: {', '.join(ALL_IMAGES)}")

    # ECR login
    info("Logging into ECR…")
    if not dry_run:
        login_pass = run(
            ["aws", "ecr", "get-login-password"],
            capture=True,
        )
        run(
            ["docker", "login", "--username", "AWS", "--password-stdin", registry],
            check=True,
            stdin_text=login_pass.stdout,
        )
    success("ECR login successful")

    # Build, tag, push
    for target in targets:
        image_name = f"kira-{target}"
        full_tag_sha = f"{registry}/{image_name}:{sha}"
        full_tag_latest = f"{registry}/{image_name}:latest"

        if target == "web-app":
            build_ctx = str(ROOT / "web-app")
        else:
            build_ctx = str(ROOT / "services" / target)

        info(f"Building {image_name}…")
        if dry_run:
            info(f"[dim](dry-run) Would build and push {full_tag_sha}[/]")
            continue

        run(["docker", "build", "-t", image_name, build_ctx])
        run(["docker", "tag", image_name, full_tag_sha])
        run(["docker", "tag", image_name, full_tag_latest])
        run(["docker", "push", full_tag_sha])
        run(["docker", "push", full_tag_latest])
        success(f"  {image_name} → {sha}")

    # kubectl apply
    overlay_path = ROOT / "k8s" / "overlays" / overlay
    info(f"Applying Kubernetes manifests ({overlay})…")
    if dry_run:
        info("[dim](dry-run) Would run: kubectl apply -k + rollout status[/]")
    else:
        run(["kubectl", "apply", "-k", str(overlay_path)])
        for target in targets:
            if target == "web-app":
                deploy_name = "web-app"
            else:
                deploy_name = target
            info(f"  Waiting for rollout: {deploy_name}…")
            run(
                [
                    "kubectl",
                    "rollout",
                    "status",
                    f"deployment/{deploy_name}",
                    "-n",
                    namespace,
                    "--timeout=300s",
                ]
            )
        success("Rollout complete")

    success(f"Deploy to {env} finished (commit {sha})")


@app.command()
def staging(
    skip_terraform: bool = typer.Option(
        False, "--skip-terraform", help="Skip Terraform phase"
    ),
    services: Optional[str] = typer.Option(
        None, "--services", help="Comma-separated list of services to deploy"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be executed without running"
    ),
) -> None:
    """Deploy to staging environment."""
    _deploy(
        "staging",
        overlay="staging",
        namespace="kira-staging",
        skip_terraform=skip_terraform,
        services=services,
        dry_run=dry_run,
    )


@app.command()
def production(
    skip_terraform: bool = typer.Option(
        False, "--skip-terraform", help="Skip Terraform phase"
    ),
    services: Optional[str] = typer.Option(
        None, "--services", help="Comma-separated list of services to deploy"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be executed without running"
    ),
) -> None:
    """Deploy to production environment.

    This will build and push Docker images to ECR, apply Terraform,
    and roll out Kubernetes deployments.
    """
    warn("You are about to deploy to PRODUCTION!")
    if not dry_run and not typer.confirm("Continue?"):
        raise typer.Abort()
    _deploy(
        "production",
        overlay="production",
        namespace="kira",
        skip_terraform=skip_terraform,
        services=services,
        dry_run=dry_run,
    )
