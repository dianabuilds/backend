from __future__ import annotations

from typing import Protocol
from uuid import UUID


class IAccessRepository(Protocol):
    async def has_purchase(
        self, *, quest_id, user_id: UUID, workspace_id: UUID
    ) -> bool:  # pragma: no cover - контракт
        ...

    async def grant_premium_days(self, *, user, days: int) -> None:  # pragma: no cover - контракт
        ...
