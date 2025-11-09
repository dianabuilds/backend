from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any


@dataclass(frozen=True, slots=True)
class ComponentDescriptor:
    key: str
    title: str
    section: str
    locales: tuple[str, ...]
    schema_file: str
    description: str | None = None
    thumbnail_url: str | None = None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ComponentSummary:
    key: str
    title: str
    section: str
    locales: tuple[str, ...]
    description: str | None
    version: str
    thumbnail_url: str | None


@dataclass(frozen=True, slots=True)
class ComponentSchema(ComponentSummary):
    schema: Mapping[str, Any]


_COMPONENTS: dict[str, ComponentDescriptor] = {
    "header": ComponentDescriptor(
        key="header",
        title="Site Global Header",
        section="header",
        description="Конфигурация глобального хедера публичного сайта.",
        locales=("ru", "en"),
        schema_file="shared_blocks/header.schema.json",
        thumbnail_url=None,
        aliases=("site_global_header", "global_header"),
    ),
}


def _iter_descriptors():
    return sorted(_COMPONENTS.values(), key=lambda item: item.key)


def _require_descriptor(key: str) -> ComponentDescriptor:
    normalized = key.strip().lower()
    if not normalized:
        raise KeyError("component_key_empty")
    if normalized in _COMPONENTS:
        return _COMPONENTS[normalized]
    # try aliases
    for descriptor in _COMPONENTS.values():
        if normalized in descriptor.aliases:
            return descriptor
    raise KeyError(f"component_not_found:{key}")


def _schema_package():
    return resources.files(__package__)


@lru_cache(maxsize=32)
def _load_schema_payload(key: str) -> tuple[dict[str, Any], str]:
    descriptor = _require_descriptor(key)
    base = _schema_package()
    path = base.joinpath(descriptor.schema_file)
    if not path.is_file():
        raise FileNotFoundError(
            f"Schema file '{descriptor.schema_file}' is missing for component '{key}'"
        )
    text = path.read_text("utf-8")
    schema = json.loads(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    version = digest[:12]
    return schema, version


def list_component_summaries() -> list[ComponentSummary]:
    summaries: list[ComponentSummary] = []
    for descriptor in _iter_descriptors():
        _, version = _load_schema_payload(descriptor.key)
        summaries.append(
            ComponentSummary(
                key=descriptor.key,
                title=descriptor.title,
                section=descriptor.section,
                locales=descriptor.locales,
                description=descriptor.description,
                version=version,
                thumbnail_url=descriptor.thumbnail_url,
            )
        )
    return summaries


def get_component_summary(key: str) -> ComponentSummary:
    descriptor = _require_descriptor(key)
    _, version = _load_schema_payload(descriptor.key)
    return ComponentSummary(
        key=descriptor.key,
        title=descriptor.title,
        section=descriptor.section,
        locales=descriptor.locales,
        description=descriptor.description,
        version=version,
        thumbnail_url=descriptor.thumbnail_url,
    )


def get_component_schema(key: str) -> ComponentSchema:
    descriptor = _require_descriptor(key)
    schema, version = _load_schema_payload(descriptor.key)
    return ComponentSchema(
        key=descriptor.key,
        title=descriptor.title,
        section=descriptor.section,
        locales=descriptor.locales,
        description=descriptor.description,
        version=version,
        thumbnail_url=descriptor.thumbnail_url,
        schema=schema,
    )


__all__ = [
    "ComponentDescriptor",
    "ComponentSchema",
    "ComponentSummary",
    "get_component_schema",
    "get_component_summary",
    "list_component_summaries",
]
