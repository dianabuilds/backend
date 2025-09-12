from __future__ import annotations

from typing import Protocol
from uuid import UUID


class IProfileRepository(Protocol):
    async def get_display(self, user_id: UUID) -> dict | None:  # pragma: no cover - contract
        ...

    async def update_fields(self, user_id: UUID, data: dict) -> dict:  # pragma: no cover - contract
        ...

__all__ = ["IProfileRepository"]

