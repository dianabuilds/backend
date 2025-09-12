from __future__ import annotations

from app.kernel.cache.utils import cache_key


def node_key(slug: str) -> str:
    return cache_key("node", slug)


__all__ = ["node_key"]

