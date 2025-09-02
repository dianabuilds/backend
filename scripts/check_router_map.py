from __future__ import annotations

import os
import sys
import types
from pathlib import Path

from fastapi.routing import APIRoute

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "apps" / "backend"
sys.path.insert(0, str(APP_DIR))

SNAPSHOT_FILE = PROJECT_ROOT / "tests" / "snapshots" / "router_map.txt"
ALLOWED_NESTED = {"/tags/tags/", "/tags/tags/{slug}"}


def build_app():
    os.environ.setdefault("DATABASE__HOST", "localhost")
    os.environ.setdefault("DATABASE__PORT", "5432")
    os.environ.setdefault("DATABASE__NAME", "app")
    os.environ.setdefault("DATABASE__USERNAME", "app")
    os.environ.setdefault("DATABASE__PASSWORD", "postgres")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("APP_CORS_ALLOW_ORIGINS", "*")

    editorjs = types.ModuleType("app.domains.nodes.application.editorjs_renderer")
    editorjs.collect_unknown_blocks = lambda *a, **k: []
    editorjs.render_html = lambda *a, **k: ""
    sys.modules.setdefault("app.domains.nodes.application.editorjs_renderer", editorjs)

    jsonschema_mod = types.ModuleType("jsonschema")

    class ValidationError(Exception):
        pass

    jsonschema_mod.ValidationError = ValidationError
    sys.modules.setdefault("jsonschema", jsonschema_mod)

    from app.main import app

    return app


def main() -> int:
    app = build_app()
    paths = sorted({route.path for route in app.routes if isinstance(route, APIRoute)})
    expected = SNAPSHOT_FILE.read_text().splitlines()
    current = set(paths)
    expected_set = set(expected)
    missing = sorted(expected_set - current)
    extra = sorted(current - expected_set)
    if missing or extra:
        if missing:
            print("Missing routes:")
            for p in missing:
                print(f"  {p}")
        if extra:
            print("Unexpected routes:")
            for p in extra:
                print(f"  {p}")
        return 1

    for path in paths:
        segments = [s for s in path.split("/") if s]
        for a, b in zip(segments, segments[1:], strict=False):
            if a == b and path not in ALLOWED_NESTED:
                print(f"Unexpected nesting detected in path: {path}")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
