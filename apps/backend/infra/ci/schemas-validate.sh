#!/usr/bin/env bash
set -euo pipefail

python <<'PY'
import json
from pathlib import Path
import sys

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print(f"[schemas] PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(1)

root = Path('apps/backend/packages/schemas')
if not root.exists():
    print('[schemas] directory not found, nothing to validate')
    sys.exit(0)

files = [
    *root.rglob('*.json'),
    *root.rglob('*.yaml'),
    *root.rglob('*.yml'),
]
if not files:
    print('[schemas] no schema files found')
    sys.exit(0)

errors: list[tuple[Path, Exception]] = []
for path in files:
    try:
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.json':
            json.loads(text)
        else:
            yaml.safe_load(text)
    except Exception as exc:
        errors.append((path, exc))

if errors:
    for path, exc in errors:
        print(f"[schemas] invalid schema {path}: {exc}", file=sys.stderr)
    sys.exit(1)

print(f"[schemas] validated {len(files)} files")
PY

