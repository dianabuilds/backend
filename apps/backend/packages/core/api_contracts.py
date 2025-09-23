from __future__ import annotations

from pathlib import Path
from typing import Any

try:  # optional deps
    import yaml
    from jsonschema import validate as jsonschema_validate
except Exception:  # pragma: no cover
    yaml = None
    jsonschema_validate = None


def _load_openapi_yaml(rel_path: str) -> dict[str, Any] | None:
    base = Path("apps/backend/packages/schemas/api")
    p = base / rel_path
    if not p.exists() or yaml is None:
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _find_request_schema(spec: dict[str, Any], path: str, method: str) -> dict[str, Any] | None:
    paths = spec.get("paths") or {}
    node = paths.get(path) or {}
    op = node.get(method.lower()) or {}
    rb = op.get("requestBody") or {}
    content = rb.get("content") or {}
    app_json = content.get("application/json") or {}
    schema = app_json.get("schema")
    if isinstance(schema, dict):
        return schema
    return None


def validate_notifications_request(path: str, method: str, payload: dict[str, Any]) -> None:
    """Validate payload for Notifications API using bundled OpenAPI schema.

    Uses apps/backend/packages/schemas/api/notifications/notifications.v1.yaml.
    No-op if dependencies or schema missing.
    """
    if jsonschema_validate is None:
        return
    spec = _load_openapi_yaml("notifications/notifications.v1.yaml")
    if not spec:
        return
    schema = _find_request_schema(spec, path, method)
    if not schema:
        return
    jsonschema_validate(instance=payload, schema=schema)


__all__ = ["validate_notifications_request"]
