#!/usr/bin/env bash
# scripts/test_integration.sh — Run integration tests with real infra
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="$ROOT/docker/docker-compose.yml"
compose() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

SERVICES=(admin-service identity-service rate-inventory-service reservation-service channel-engine notification-service)

cleanup() {
  echo ""
  echo "=== Tearing down integration infra ==="
  compose down postgres redis kafka 2>/dev/null || true
}
trap cleanup EXIT

echo "=== Starting integration infrastructure ==="
compose up -d postgres redis kafka

echo "=== Waiting for Postgres ==="
for i in $(seq 1 30); do
  compose exec -T postgres pg_isready -U postgres -d kira >/dev/null 2>&1 && break
  sleep 1
done

echo "=== Running integration tests ==="
FAILED=()
for svc in "${SERVICES[@]}"; do
  skip=0
  for s in ${SKIP_TEST_SERVICES:-}; do
    if [ "$s" = "$svc" ]; then skip=1; break; fi
  done
  if [ "$skip" -eq 1 ]; then
    echo ""
    echo "--- Skipping integration: $svc (SKIP_TEST_SERVICES) ---"
    continue
  fi
  echo ""
  echo "--- Integration: $svc ---"
  if ! (cd "services/$svc" && uv run pytest -v -m integration); then
    FAILED+=("$svc")
  fi
done

echo ""
if [ ${#FAILED[@]} -gt 0 ]; then
  echo "FAILED: ${FAILED[*]}"
  exit 1
else
  echo "All integration tests passed."
fi
