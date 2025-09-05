from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol


class IRateLimiter(Protocol):
    def dependency(self, key: str | None = None) -> Callable[..., Any]:  # pragma: no cover
        ...
