from __future__ import annotations

from typing import Any, Dict, Protocol
from uuid import UUID


class ITagAdminRepository(Protocol):
    async def add_alias(self, tag_id: UUID, alias_norm: str, type_: str = "synonym") -> object:  # pragma: no cover
        ...

    async def remove_alias(self, alias_id: UUID) -> None:  # pragma: no cover
        ...

    async def list_aliases(self, tag_id: UUID) -> list[object]:  # pragma: no cover
        ...

    async def dry_run_merge(self, from_id: UUID, to_id: UUID) -> Dict[str, Any]:  # pragma: no cover
        ...

    async def apply_merge(self, from_id: UUID, to_id: UUID, actor_id: str | None, reason: str | None) -> Dict[str, Any]:  # pragma: no cover
        ...
