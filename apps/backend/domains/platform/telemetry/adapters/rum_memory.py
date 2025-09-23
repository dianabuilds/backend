from __future__ import annotations

import asyncio
from collections import deque
from typing import Any

from domains.platform.telemetry.ports.rum_port import IRumRepository


class RumMemoryRepository(IRumRepository):
    def __init__(self, *, maxlen: int = 1000) -> None:
        self._buf: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = asyncio.Lock()

    async def add(self, event: dict[str, Any]) -> None:
        async with self._lock:
            self._buf.appendleft(dict(event))

    async def list(self, limit: int) -> list[dict[str, Any]]:
        async with self._lock:
            out = list(self._buf)[: max(0, int(limit))]
        return [dict(it) for it in out]


__all__ = ["RumMemoryRepository"]
