#!/usr/bin/env bash
set -euo pipefail

# CI gate to ensure no legacy imports leak into DDD codebase.
# For now, we only assert that DDD code does not import the monolith.

if grep -R "from app\.\|apps/backend/app" apps/backendDDD >/dev/null 2>&1; then
  echo "ERROR: DDD code references monolith packages" >&2
  exit 1
fi

echo "Legacy check passed (no monolith imports in DDD)."
