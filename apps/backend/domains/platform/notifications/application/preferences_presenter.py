from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict


class PreferencesResponse(TypedDict):
    preferences: dict[str, Any]


class AckResponse(TypedDict):
    ok: bool


def build_preferences_response(preferences: Mapping[str, Any]) -> PreferencesResponse:
    return PreferencesResponse(preferences=dict(preferences))


def build_ack_response() -> AckResponse:
    return AckResponse(ok=True)


__all__ = [
    "AckResponse",
    "PreferencesResponse",
    "build_ack_response",
    "build_preferences_response",
]
