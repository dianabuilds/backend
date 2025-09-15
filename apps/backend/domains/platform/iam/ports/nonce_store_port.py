from __future__ import annotations

from typing import Protocol


class NonceStore(Protocol):
    async def issue(self, user_id: str, ttl_seconds: int = 600) -> str: ...
    async def verify(self, user_id: str, nonce: str) -> bool: ...


__all__ = ["NonceStore"]
