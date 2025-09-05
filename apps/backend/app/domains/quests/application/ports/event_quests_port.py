from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID


class IEventQuestsRepository(Protocol):
    async def get_active_for_node(
        self, workspace_id: UUID, now: datetime, node_id
    ) -> Sequence[object]:  # pragma: no cover - контракт
        ...

    async def has_completion(
        self, quest_id, user_id, workspace_id: UUID
    ) -> bool:  # pragma: no cover - контракт
        ...

    async def create_completion(
        self, quest_id, user_id, node_id, workspace_id: UUID
    ) -> object:  # pragma: no cover - контракт
        ...

    async def count_completions(
        self, quest_id, workspace_id: UUID
    ) -> int:  # pragma: no cover - контракт
        ...
