#!/usr/bin/env bash
set -euo pipefail

# Resolve repository and app roots
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPO_ROOT="$(cd "$APP_ROOT/../.." && pwd)"

# Load environment from .env files if present (without leaking values)
source_if_exists() {
  local f="$1"
  if [[ -f "$f" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$f"
    set +a
  fi
}

# Load in order: repo .env, repo .env.local, app .env, app .env.local
source_if_exists "$REPO_ROOT/.env"
source_if_exists "$REPO_ROOT/.env.local"
source_if_exists "$APP_ROOT/.env"
source_if_exists "$APP_ROOT/.env.local"

# Determine DB URL: prefer APP_DATABASE_URL/DB_URL, otherwise compose from DATABASE__*
DB_URL="${APP_DATABASE_URL:-${DB_URL:-}}"
if [[ -z "${DB_URL}" ]]; then
  USERNAME="${DATABASE__USERNAME:-}"
  PASSWORD="${DATABASE__PASSWORD:-}"
  HOST="${DATABASE__HOST:-}"
  PORT="${DATABASE__PORT:-5432}"
  NAME="${DATABASE__NAME:-}"
  SSLMODE="${DATABASE__SSLMODE:-}"

  if [[ -n "$USERNAME" && -n "$HOST" && -n "$NAME" ]]; then
    local_pw=""
    if [[ -n "$PASSWORD" ]]; then
      local_pw=":$PASSWORD"
    fi
    local_q=""
    if [[ -n "$SSLMODE" ]]; then
      local_q="?sslmode=$SSLMODE"
    fi
    DB_URL="postgresql://$USERNAME$local_pw@$HOST:$PORT/$NAME$local_q"
  fi
fi

if [[ -z "$DB_URL" ]]; then
  echo "ERROR: Database URL is not set. Configure APP_DATABASE_URL or DATABASE__* in .env" >&2
  exit 1
fi

shopt -s nullglob
ROOT="$APP_ROOT/domains"

# Collect all *.sql files under domains/*/schema/sql, sorted
mapfile -t FILES < <(find "$ROOT" -type d -path "*/schema/sql" -print0 | xargs -0 -I{} find {} -maxdepth 1 -type f -name "*.sql" | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No SQL files to migrate." >&2
  exit 0
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "ERROR: 'psql' is required to run DDL migrations. Install PostgreSQL client or run in a container/WSL." >&2
  exit 2
fi

echo "Applying SQL migrations..." >&2
for f in "${FILES[@]}"; do
  echo "  -> $f" >&2
  psql "$DB_URL" -v ON_ERROR_STOP=1 -f "$f"
done
echo "Done." >&2
