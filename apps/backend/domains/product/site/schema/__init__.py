from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import resources
from typing import Any

_GLOBAL_BLOCKS_PACKAGE = resources.files(__package__).joinpath("global_blocks")


def available_global_block_schemas() -> list[str]:
    """Return a sorted list of available global block schema names."""
    if not _GLOBAL_BLOCKS_PACKAGE.is_dir():
        return []
    names: list[str] = []
    for entry in _GLOBAL_BLOCKS_PACKAGE.iterdir():
        if entry.is_file() and entry.name.endswith(".schema.json"):
            names.append(entry.name.removesuffix(".schema.json"))
    names.sort()
    return names


def load_global_block_schema(name: str) -> Mapping[str, Any]:
    """Load JSON schema for a global block template."""
    normalized = name.strip().lower().replace("-", "_")
    if not normalized:
        raise ValueError("Schema name must be a non-empty string")
    candidate = f"{normalized}.schema.json"
    path = _GLOBAL_BLOCKS_PACKAGE.joinpath(candidate)
    if not path.is_file():
        raise FileNotFoundError(f"Schema for global block '{name}' is not available")
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


__all__ = ["available_global_block_schemas", "load_global_block_schema"]
