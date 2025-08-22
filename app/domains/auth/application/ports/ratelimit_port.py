from __future__ import annotations

from typing import Protocol, Callable, Any


class IRateLimiter(Protocol):
    def dependency(self, key: str | None = None) -> Callable[..., Any]:  # pragma: no cover
        ...
