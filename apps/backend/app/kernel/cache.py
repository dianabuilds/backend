from __future__ import annotations

import abc
from typing import Any, Optional


class AbstractAsyncCache(abc.ABC):
    @abc.abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abc.abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        pass

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abc.abstractmethod
    async def incr(self, key: str, amount: int = 1, ttl: Optional[float] = None) -> int:
        pass

    @abc.abstractmethod
    async def expire(self, key: str, ttl: float) -> bool:
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        pass


__all__ = [
    "AbstractAsyncCache",
]

