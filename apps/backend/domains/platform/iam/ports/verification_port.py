from __future__ import annotations

from typing import Protocol


class VerificationTokenStore(Protocol):
    async def create(self, email: str, ttl_seconds: int = 86400) -> str: ...
    async def verify(self, token: str) -> str | None: ...  # returns email


__all__ = ["VerificationTokenStore"]
