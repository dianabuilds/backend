from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.api_gateway.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI spec to JSON")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("apps/apps/backend/var/openapi.json"),
        help="Output path for openapi.json",
    )
    args = parser.parse_args()
    spec = app.openapi()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OpenAPI exported to {args.out}")


if __name__ == "__main__":
    main()
