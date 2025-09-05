from __future__ import annotations

from typing import Any, Protocol


class IRumRepository(Protocol):
    async def add(self, event: dict[str, Any]) -> None:  # pragma: no cover - interface
        ...

    async def list(self, limit: int) -> list[dict[str, Any]]:  # pragma: no cover - interface
        ...
