from __future__ import annotations

from typing import List, Optional, Protocol


class IKeyValueCache(Protocol):
    async def get(self, key: str) -> Optional[str]:  # pragma: no cover - контракт
        ...

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:  # pragma: no cover - контракт
        ...

    async def delete(self, *keys: str) -> None:  # pragma: no cover - контракт
        ...

    async def scan(self, pattern: str) -> List[str]:  # pragma: no cover - контракт
        ...
