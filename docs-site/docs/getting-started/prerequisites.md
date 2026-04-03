---
title: Prerequisites
description: Everything you need to install before running KIRA locally — Docker, Python, uv, bun, and recommended tooling.
sidebar_position: 1
---

# Prerequisites

**What you'll learn:**
- Which tools are required and which versions to use
- How to install each tool on macOS and Linux
- Recommended hardware and IDE setup
- How to verify your environment is ready

:::info Before you start
KIRA runs entirely in Docker Compose for local development. You do **not** need to install PostgreSQL, Redis, or Kafka directly — those run as containers. You only need the tools below on your host machine.
:::

---

## Required Tools

### Docker Desktop

The full KIRA stack runs as containers. Docker Desktop includes both the daemon and Docker Compose v2.

| Platform | Minimum Version | RAM to Allocate |
|---|---|---|
| macOS (Apple Silicon M1+) | 4.20+ | **8 GB minimum, 12 GB recommended** |
| macOS (Intel) | 4.20+ | 8 GB minimum |
| Windows (WSL2) | 4.20+ | 8 GB minimum |
| Linux | Docker Engine 24+ | 8 GB minimum |

```bash
# macOS — install via Homebrew
brew install --cask docker

# Verify
docker --version          # Docker version 24.x.x
docker compose version    # Docker Compose version v2.x.x
```

:::warning Docker Desktop memory setting
After installation, open Docker Desktop → Settings → Resources → Memory and set it to at least **8 GB**. With the default 2 GB setting, Kafka and PostgreSQL will crash or OOM-kill each other.
:::

**Post-install for Linux:** Add your user to the `docker` group so you don't need `sudo`:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

### Git

```bash
# macOS (Xcode command line tools)
xcode-select --install

# macOS via Homebrew
brew install git

# Ubuntu / Debian
sudo apt-get install git

# Verify
git --version    # git version 2.x.x
```

---

### Python 3.13+

Python is needed to run backend services outside Docker (e.g., for running a single service with hot reload during development, or running migrations directly).

```bash
# macOS — Homebrew
brew install python@3.13

# Ubuntu / Debian
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.13 python3.13-venv

# Verify
python3.13 --version    # Python 3.13.x
```

---

### uv

[uv](https://github.com/astral-sh/uv) is the Python package resolver and virtual environment manager used throughout the project. It wraps Poetry commands and is significantly faster than pip.

```bash
# macOS / Linux — official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Homebrew (macOS)
brew install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify
uv --version    # uv 0.x.x
```

After installation, restart your terminal so `uv` is in your `PATH`.

---

### Poetry

Each backend service manages its dependencies with [Poetry](https://python-poetry.org/). Poetry is invoked through uv (`uv run poetry ...`), so you install it once and uv handles the rest.

```bash
# Install via uv (recommended)
uv tool install poetry

# Or via the official installer
curl -sSL https://install.python-poetry.org | python3 -

# Verify
uv run poetry --version    # Poetry (version 1.x.x)
```

---

### bun

[bun](https://bun.sh/) is the JavaScript runtime and package manager for the frontend (`web-app/`) and the documentation site (`docs-site/`). Do **not** use `npm` or `yarn` — bun lockfiles are committed and npm/yarn will generate different lockfiles.

```bash
# macOS / Linux — official installer
curl -fsSL https://bun.sh/install | bash

# Homebrew (macOS)
brew install bun

# Windows
powershell -c "irm bun.sh/install.ps1 | iex"

# Verify
bun --version    # 1.x.x
```

---

### Node.js 20+

Node.js is required by Docusaurus (the `docs-site/` Docusaurus dev server uses it internally) and some Vite tooling. bun handles most frontend tasks, but Node.js must be present.

```bash
# macOS — Homebrew (installs LTS)
brew install node

# macOS / Linux — nvm (recommended to manage versions)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20
nvm use 20

# Verify
node --version    # v20.x.x
```

---

## Verify Your Environment

Run this quick check to confirm all tools are in place:

```bash
docker --version
docker compose version
git --version
python3.13 --version
uv --version
bun --version
node --version
```

All six commands should return version numbers without errors.

---

## Recommended: VS Code

While any editor works, VS Code with the following extensions provides the best experience:

| Extension | Publisher | Purpose |
|---|---|---|
| Python | ms-python | IntelliSense, debugger |
| Pylance | ms-python | Type checking, go-to-definition |
| Ruff | charliermarsh | Linting + formatting on save |
| ESLint | dbaeumer | TypeScript/React linting |
| Tailwind CSS IntelliSense | bradlc | Tailwind class autocomplete |
| Docker | ms-azuretools | Dockerfile syntax, container explorer |
| YAML | redhat | YAML validation (k8s manifests) |
| GitLens | eamodio | Git blame, history |

Recommended VS Code settings (add to `.vscode/settings.json` in the repo root):

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "python.linting.enabled": false,
  "ruff.lint.enable": true,
  "editor.rulers": [100]
}
```

---

## Recommended Hardware

| Spec | Minimum | Recommended |
|---|---|---|
| CPU | Apple M1 / Intel i5 8th gen | Apple M2 Pro / Intel i7 10th gen or newer |
| RAM | 16 GB | 32 GB |
| Disk | 30 GB free | 50 GB+ SSD |
| OS | macOS 13+ / Ubuntu 22.04 / Windows 11 (WSL2) | macOS 14+ / Ubuntu 24.04 |

:::tip Apple Silicon
KIRA's Docker images build natively for `linux/arm64` on Apple Silicon. Build times on M1/M2/M3 Macs are 2–3× faster than Intel Macs for the Python images.
:::

---

## Optional: AWS CLI + kubectl (for production)

Only needed if you plan to deploy to AWS EKS or interact with the staging/production clusters.

```bash
# AWS CLI v2
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
brew install awscli      # macOS
aws --version            # aws-cli/2.x.x

# kubectl
brew install kubectl     # macOS
kubectl version --client # v1.28+

# eksctl
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl
eksctl version           # 0.x.x
```

---

## Next Step

→ **[Local Setup](./local-setup.md)** — clone the repo, configure environment variables, and start the full stack.
