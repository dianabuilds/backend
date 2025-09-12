from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID


class IEventQuestsRepository(Protocol):
    async def get_active_for_node(
        self, tenant_id: UUID, now: datetime, node_id
    ) -> Sequence[object]:  # pragma: no cover - контракт
        ...

    async def has_completion(
        self, quest_id, user_id, tenant_id: UUID
    ) -> bool:  # pragma: no cover - контракт
        ...

    async def create_completion(
        self, quest_id, user_id, node_id, tenant_id: UUID
    ) -> object:  # pragma: no cover - контракт
        ...

    async def count_completions(
        self, quest_id, tenant_id: UUID
    ) -> int:  # pragma: no cover - контракт
        ...
