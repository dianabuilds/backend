from __future__ import annotations

from app.kernel.cache.utils import cache_key


def navigation_key(slug: str) -> str:
    return cache_key("navigation", slug)


__all__ = ["navigation_key"]

