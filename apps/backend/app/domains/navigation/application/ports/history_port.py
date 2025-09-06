from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class IUserHistoryStore(Protocol):
    async def load(self, user_id: str) -> tuple[list[str], list[str]]: ...

    async def save(self, user_id: str, tags: Sequence[str], slugs: Sequence[str]) -> None: ...
