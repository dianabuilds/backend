"""Helpers for validating AI related payloads."""

from __future__ import annotations

from typing import Any, Dict

import jsonschema

from app.domains.quests.validation import validate_version_graph  # noqa: F401


# JSON schema describing allowed fields for AI presets that can be configured
# per workspace. Only the listed keys are permitted and they must have the
# specified types.
AI_PRESETS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "temperature": {"type": "number"},
        "system_prompt": {"type": "string"},
        "forbidden": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def validate_ai_presets(presets: Dict[str, Any]) -> None:
    """Validate workspace AI presets against :data:`AI_PRESETS_SCHEMA`.

    Raises :class:`jsonschema.ValidationError` if presets don't conform to the
    schema.
    """

    jsonschema.validate(presets, AI_PRESETS_SCHEMA)


__all__ = ["validate_version_graph", "AI_PRESETS_SCHEMA", "validate_ai_presets"]

