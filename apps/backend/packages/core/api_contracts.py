from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

yaml: ModuleType | None
jsonschema_validate: Callable[..., None] | None

try:  # optional deps
    import yaml as _yaml
    from jsonschema import FormatChecker
    from jsonschema import validate as _jsonschema_validate
except Exception:  # pragma: no cover
    yaml = None
    jsonschema_validate = None
else:
    yaml = _yaml
    _format_checker = FormatChecker()

    def _validator(instance, schema, **kwargs):
        return _jsonschema_validate(
            instance=instance, schema=schema, format_checker=_format_checker
        )

    jsonschema_validate = _validator


def _load_openapi_yaml(rel_path: str) -> dict[str, Any] | None:
    base = Path(__file__).resolve().parent.parent / "schemas" / "api"
    p = base / rel_path
    if not p.exists() or yaml is None:
        return None
    loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        return cast(dict[str, Any], loaded)
    return None


def _find_request_schema(
    spec: dict[str, Any], path: str, method: str
) -> dict[str, Any] | None:
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


def validate_notifications_request(
    path: str, method: str, payload: dict[str, Any]
) -> None:
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
