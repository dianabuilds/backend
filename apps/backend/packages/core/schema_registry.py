from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any


def _load_jsonschema_validator() -> Callable[..., None] | None:
    try:  # optional dependency for JSON Schema
        from jsonschema import FormatChecker
        from jsonschema import validate as _validate
    except Exception:  # pragma: no cover
        return None
    format_checker = FormatChecker()

    def _validator(instance: Any, schema: dict[str, Any], **kwargs: Any) -> None:
        _validate(instance=instance, schema=schema, format_checker=format_checker)

    return _validator


jsonschema_validate: Callable[..., None] | None = _load_jsonschema_validator()


def read_schema(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def event_schema_path(topic: str) -> Path:
    # events/<domain>/<topic>.json; e.g., profile.updated.v1 -> events/profile/profile.updated.v1.json
    domain = topic.split(".", 1)[0]
    base = Path(__file__).resolve().parent.parent / "schemas" / "events"
    return base / domain / f"{topic}.json"


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
