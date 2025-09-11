from __future__ import annotations

from typing import Any

import jsonschema

from .schemas_v2 import Preset, ProviderManifest, ProviderSecrets, RoutingProfile


def validate_manifest(data: dict[str, Any]) -> None:
    jsonschema.validate(data, ProviderManifest)


def validate_routing_profile(data: dict[str, Any]) -> None:
    jsonschema.validate(data, RoutingProfile)


def validate_preset(data: dict[str, Any]) -> None:
    jsonschema.validate(data, Preset)


def validate_secrets(data: dict[str, Any]) -> None:
    jsonschema.validate(data, ProviderSecrets)


__all__ = [
    "validate_manifest",
    "validate_routing_profile",
    "validate_preset",
    "validate_secrets",
]
