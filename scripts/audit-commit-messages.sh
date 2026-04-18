#!/usr/bin/env bash
# List commit subjects that fail the current commitlint rules (non-zero exit).
# Skips merge commits. Run from repo root: bun run commit:audit

set -euo pipefail
cd "$(dirname "$0")/.."
failures=0
while IFS= read -r line; do
  [[ "$line" == Merge\ * ]] && continue
  if ! echo "$line" | bunx commitlint >/dev/null 2>&1; then
    echo "FAIL: $line"
    failures=$((failures + 1))
  fi
done < <(git log --format='%s')

if [[ "$failures" -eq 0 ]]; then
  echo "All non-merge commit subjects pass commitlint."
else
  echo >&2 ""
  echo >&2 "Found $failures failing commit(s). Rewriting published history breaks clones and PRs;"
  echo >&2 "fix only unpushed commits (git rebase -i) or leave old commits as-is and enforce rules going forward."
  exit 1
fi
