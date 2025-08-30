#!/usr/bin/env bash
set -euo pipefail

if [ -d legacy ]; then
  if git ls-files legacy | grep -q .; then
    echo "Legacy directory must remain empty. Remove the following files:" >&2
    git ls-files legacy >&2
    exit 1
  fi
fi

