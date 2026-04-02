# KIRA — Claude Code Setup

## What's here

```
claude-code-setup/
├── CLAUDE.md                → Copy to repo root: kira/CLAUDE.md
├── .claude/rules/
│   ├── backend.md           → Copy to: kira/.claude/rules/backend.md
│   ├── frontend.md          → Copy to: kira/.claude/rules/frontend.md
│   └── infrastructure.md    → Copy to: kira/.claude/rules/infrastructure.md
├── PROMPTS.md               → Keep open, paste prompts into Claude Code
└── README.md                → This file
```

## Setup

1. `mkdir kira && cd kira && git init`
2. Copy `CLAUDE.md` to repo root
3. Copy `.claude/` folder to repo root
4. Copy your `coding-blueprint/` docs to `docs/coding-blueprint/`
5. Open Claude Code (`claude` CLI or VS Code extension)
6. Paste prompts from `PROMPTS.md` one at a time

## Key rules enforced

- Claude will NEVER run commands — only generates files and folders
- Backend uses Poetry with uv (not pip, not requirements.txt)
- Frontend uses bun (not npm, not yarn, not pnpm)
- Project name: KIRA (everywhere)

## Prompt order (15 prompts, 5 phases)

| # | Prompt | Builds |
|---|--------|--------|
| 0.1 | Monorepo skeleton | All folders + pyproject.toml + Dockerfiles |
| 0.2 | Docker Compose | docker-compose.yml, kong.yml, Makefile, observability |
| 0.3 | Shared package | Security, events, crypto, middleware |
| 1.1 | Identity: models | User, RefreshToken, AuditEvent + Pydantic schemas |
| 1.2 | Identity: full | Repos, services, routers, tests (auth + users + audit) |
| 1.3 | Admin service | Tenant onboarding, config, schema provisioning |
| 2.1 | Rate & Inventory | Rooms, rates, ARI calendar, seasonal rules, Kafka events |
| 2.2 | Reservation | Bookings, guests, inbox, modification, cancellation |
| 3.1 | Channel Engine | OTA adapters, ARI sync, retry, circuit breaker |
| 3.2 | Notification | Alerts, email, Kafka consumers, preferences |
| 4.1 | React scaffold | Vite + bun + Tailwind + routing + layout + shared components |
| 4.2 | Auth + Dashboard | Login, MFA, KPI cards, charts |
| 4.3 | Core screens | Rooms, inventory calendar, reservations inbox |
| 4.4 | Remaining screens | Channels, notifications, settings |
| 5.1 | CI/CD + K8s | GitHub Actions per service + K8s manifests |
