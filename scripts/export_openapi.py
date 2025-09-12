from __future__ import annotations

"""
Export OpenAPI schema to docs/openapi/openapi.json.

Usage:
  cd backend && python scripts/export_openapi.py

Notes:
- Uses ENVIRONMENT=development to include all domain routers.
- Does not run startup events; only imports the app and renders schema.
"""

import json
import os
import sys
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    # Ensure "app" package is importable (apps/backend on PYTHONPATH)
    sys.path.insert(0, str(base_dir / "apps" / "backend"))
    # Ensure full router set
    os.environ.setdefault("ENVIRONMENT", "development")

    from fastapi.openapi.utils import get_openapi
    from app.main import app

    schema = get_openapi(
        title="Backend API",
        version="1.0.0",
        routes=app.routes,
    )

    out_dir = base_dir / "docs" / "openapi"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "openapi.json"
    out_file.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OpenAPI exported to {out_file}")


if __name__ == "__main__":
    main()

