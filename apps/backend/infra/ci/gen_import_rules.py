from __future__ import annotations

import glob
from pathlib import Path

import yaml


def main() -> int:
    # Scan domain registry and emit import-linter layer rules
    print("[importlinter]")
    print("root_package = apps")
    print()
    for f in glob.glob("apps/apps/backend/packages/domain-registry/*.yaml"):
        if f.endswith("index.yaml"):
            continue
        spec = yaml.safe_load(open(f, encoding="utf-8"))
        # File name is domain name (e.g., profile.yaml) and spec.type is kind (product/platform)
        name = Path(f).stem
        kind = (spec.get("type") or "product").strip()
        base = f"apps.apps/backend.domains.{kind}.{name}"
        print(f"[contract:layers_{kind}_{name}]")
        print(f"name = layers for {kind}/{name}")
        print("type = layers")
        print("layers =")
        for layer in spec.get("layers", []):
            print(f"    {base}.{layer}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
