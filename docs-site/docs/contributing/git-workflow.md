---
sidebar_position: 4
---

# Git Workflow

## Branch Naming

```
feat/<service>-<feature>       # new feature
fix/<service>-<bug>            # bug fix
chore/<scope>-<description>    # maintenance, dependencies, docs
refactor/<service>-<what>      # code refactor without behavior change
```

Examples:
- `feat/channel-engine-booking-com-adapter`
- `fix/identity-service-refresh-token-rotation`
- `chore/k8s-update-hpa-config`
- `feat/web-app-bulk-ari-update`

## Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

Optional longer description.

BREAKING CHANGE: describe if applicable
```

Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`

Examples:
```
feat(channel-engine): add Booking.com ARI push adapter
fix(identity-service): refresh token not rotated on reuse
chore(k8s): increase production HPA max replicas to 8
test(reservation-service): add cancellation policy edge cases
```

## Pull Request Process

1. **Branch from main** — keep branches short-lived
2. **Write tests** — coverage must not drop below 70%
3. **Update docs** — if your change affects the API or architecture
4. **Open PR** — fill in the PR template (summary + test plan)
5. **CI must pass** — all tests, lint, coverage gate
6. **1 review required** — from a team member
7. **Squash merge** — keeps main history clean

## PR Template

```markdown
## Summary
- What does this PR do?
- Why is this change needed?

## Changes
- List key files changed

## Test Plan
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual test steps (if relevant)

## Deployment Notes
- Any migration needed?
- Any env var changes?
- Any breaking API changes?
```

## Never Commit

- `.env` files
- Secret keys or API credentials
- `node_modules/`
- `.venv/` or virtualenv directories
- Build artifacts (`dist/`, `__pycache__/`, `.pytest_cache/`)

These are all covered by `.gitignore` but worth repeating.

## Merge Freeze

Check with the team before merging non-critical changes during:
- Mobile release cuts
- Major OTA integration deployments
- On-call escalation periods
