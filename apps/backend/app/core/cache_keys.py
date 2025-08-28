from __future__ import annotations

from app.core.config import settings


def cache_key(*parts: str) -> str:
    """Build a namespaced cache key using configured key version."""
    return ":".join([settings.cache.key_version, *[str(p) for p in parts]])


def node_key(slug: str) -> str:
    """Cache key for a node by slug."""
    return cache_key("node", slug)


def quest_version_key(version_id: str) -> str:
    """Cache key for a quest version by id."""
    return cache_key("questVersion", version_id)


def navigation_key(slug: str) -> str:
    """Cache key for navigation data of a node slug."""
    return cache_key("navigation", slug)


__all__ = [
    "cache_key",
    "node_key",
    "quest_version_key",
    "navigation_key",
]
