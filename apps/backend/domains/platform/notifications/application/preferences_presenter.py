from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_preferences_response(preferences: Mapping[str, Any]) -> dict[str, Any]:
    return {"preferences": dict(preferences)}


def build_ack_response() -> dict[str, Any]:
    return {"ok": True}


__all__ = ["build_ack_response", "build_preferences_response"]
