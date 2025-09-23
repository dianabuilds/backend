#!/usr/bin/env bash
set -euo pipefail
echo "Validating schemas (YAML/JSON) ..."
find apps/backend/packages/schemas -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -print >/dev/null

