#!/usr/bin/env bash
set -euo pipefail

DB_URL="${APP_DATABASE_URL:-${DB_URL:-}}"
if [[ -z "$DB_URL" ]]; then
  echo "ERROR: set APP_DATABASE_URL or DB_URL" >&2
  exit 1
fi

shopt -s nullglob
# Root for domain SQL DDL files (moved from backendDDD -> backend)
ROOT="apps/backend/domains"

# Collect all *.sql files under domains/*/schema/sql, sorted
mapfile -t FILES < <(find "$ROOT" -type d -path "*/schema/sql" -print0 | xargs -0 -I{} find {} -maxdepth 1 -type f -name "*.sql" | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No SQL files to migrate." >&2
  exit 0
fi

echo "Applying SQL migrations to $DB_URL" >&2
for f in "${FILES[@]}"; do
  echo "  -> $f" >&2
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$f"
done
echo "Done." >&2
