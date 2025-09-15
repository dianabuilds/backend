from __future__ import annotations

from typing import Any, Protocol


class IRumRepository(Protocol):
    async def add(self, event: dict[str, Any]) -> None: ...

    async def list(self, limit: int) -> list[dict[str, Any]]: ...


__all__ = ["IRumRepository"]
