from __future__ import annotations

from pathlib import Path
from typing import Any

try:  # optional dependency for JSON Schema
    import json

    from jsonschema import Draft202012Validator
    from jsonschema import validate as jsonschema_validate
except Exception:  # pragma: no cover
    jsonschema_validate = None
    Draft202012Validator = None


def read_schema(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def event_schema_path(topic: str) -> Path:
    # events/<domain>/<topic>.json; e.g., profile.updated.v1 -> events/profile/profile.updated.v1.json
    domain = topic.split(".", 1)[0]
    return Path("apps/apps/backend/packages/schemas/events") / domain / f"{topic}.json"


def load_event_schema(topic: str) -> dict[str, Any] | None:
    p = event_schema_path(topic)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def validate_event_payload(topic: str, payload: dict[str, Any]) -> None:
    schema = load_event_schema(topic)
    if not schema or jsonschema_validate is None:
        return
    jsonschema_validate(instance=payload, schema=schema)
