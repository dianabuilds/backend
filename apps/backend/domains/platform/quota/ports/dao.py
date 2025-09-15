from __future__ import annotations

from typing import Protocol


class QuotaDAO(Protocol):
    async def incr(
        self, *, user_id: str, key: str, period: str, amount: int, ttl: int
    ) -> int: ...

    async def get(self, *, user_id: str, key: str, period: str) -> int: ...


__all__ = ["QuotaDAO"]
