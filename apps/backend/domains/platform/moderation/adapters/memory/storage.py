from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

__all__ = ["InMemoryModerationStorage"]


class InMemoryModerationStorage:
    """In-process snapshot store used for tests and demo environments."""

    def __init__(self) -> None:
        self._payload: dict[str, Any] | None = None
        self._lock = asyncio.Lock()

    def enabled(self) -> bool:
        return True

    async def load(self) -> dict[str, Any]:
        async with self._lock:
            return dict(self._payload or {})

    async def save(self, payload: Mapping[str, Any]) -> None:
        async with self._lock:
            self._payload = dict(payload)
