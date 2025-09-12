from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class ISlugService(Protocol):
    async def unique_slug(
        self, db: AsyncSession, base: str, author_id: UUID, *, skip_node_id: int | None = None
    ) -> str:  # pragma: no cover
        ...


__all__ = ["ISlugService"]

