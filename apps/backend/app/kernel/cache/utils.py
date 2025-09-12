from __future__ import annotations

from app.kernel.config import settings


def cache_key(*parts: object) -> str:
    """Build a namespaced cache key using configured key version.

    Accepts arbitrary parts, casts them to str, and joins with ':'
    prefixed by the cache key version.
    """

    return ":".join([settings.cache.key_version, *[str(p) for p in parts]])


__all__ = ["cache_key"]

