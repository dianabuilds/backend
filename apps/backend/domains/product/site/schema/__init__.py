from __future__ import annotations

import json
from collections.abc import Mapping
from importlib import resources
from typing import Any

_SHARED_BLOCKS_PACKAGE = resources.files(__package__).joinpath("shared_blocks")


def available_shared_block_schemas() -> list[str]:
    """Return a sorted list of available shared block schema names."""
    if not _SHARED_BLOCKS_PACKAGE.is_dir():
        return []
    names: list[str] = []
    for entry in _SHARED_BLOCKS_PACKAGE.iterdir():
        if entry.is_file() and entry.name.endswith(".schema.json"):
            names.append(entry.name.removesuffix(".schema.json"))
    names.sort()
    return names


def load_shared_block_schema(name: str) -> Mapping[str, Any]:
    """Load JSON schema for a shared block template."""
    normalized = name.strip().lower().replace("-", "_")
    if not normalized:
        raise ValueError("Schema name must be a non-empty string")
    candidate = f"{normalized}.schema.json"
    path = _SHARED_BLOCKS_PACKAGE.joinpath(candidate)
    if not path.is_file():
        raise FileNotFoundError(f"Schema for shared block '{name}' is not available")
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


__all__ = ["available_shared_block_schemas", "load_shared_block_schema"]
