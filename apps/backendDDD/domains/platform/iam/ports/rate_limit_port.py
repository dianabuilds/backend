from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

RateDep = Callable[..., Awaitable[None]]


class RateLimiter(Protocol):
    def dependency(self, key: str) -> RateDep: ...


__all__ = ["RateLimiter", "RateDep"]
