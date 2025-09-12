from __future__ import annotations

from app.kernel.cache.utils import cache_key


def quest_version_key(version_id: str) -> str:
    return cache_key("questVersion", version_id)


__all__ = ["quest_version_key"]

