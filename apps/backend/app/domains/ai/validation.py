"""Helpers for validating AI related payloads."""

from __future__ import annotations

from typing import Any

import jsonschema

from app.domains.quests.validation import validate_version_graph  # noqa: F401

# JSON schema describing allowed fields for AI presets that can be configured
# globally or per user/profile. Only the listed keys are permitted and they
# must have the specified types.
AI_PRESETS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "model": {"type": "string"},
        "provider": {"type": "string"},
        "temperature": {"type": "number"},
        "system_prompt": {"type": "string"},
        "forbidden": {
            "type": "array",
            "items": {"type": "string"},
        },
        "allowed_models": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def validate_ai_presets(presets: dict[str, Any]) -> None:
    """Validate AI presets against :data:`AI_PRESETS_SCHEMA`.

    Raises :class:`jsonschema.ValidationError` if presets don't conform to the
    schema.
    """

    jsonschema.validate(presets, AI_PRESETS_SCHEMA)


__all__ = ["validate_version_graph", "AI_PRESETS_SCHEMA", "validate_ai_presets"]
