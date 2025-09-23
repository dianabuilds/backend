#!/usr/bin/env bash
set -euo pipefail

KIND="${1:-}"
NAME="${2:-}"

if [[ -z "$KIND" || -z "$NAME" ]]; then
  echo "Usage: gen_domain.sh <platform|product> <name>" >&2
  exit 1
fi

ROOT="apps/backend/domains"
SRC="$ROOT/$KIND/_template"
DST="$ROOT/$KIND/$NAME"

if [[ ! -d "$SRC" ]]; then
  echo "Template not found: $SRC" >&2
  exit 1
fi
if [[ -e "$DST" ]]; then
  echo "Destination already exists: $DST" >&2
  exit 1
fi

mkdir -p "$DST"
cp -R "$SRC/"* "$DST/" || true
echo "Created domain skeleton: $DST"
echo "Review files for placeholders and update wires/routers as needed."
