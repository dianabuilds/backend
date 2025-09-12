from __future__ import annotations

import hashlib
from typing import Final
from uuid import UUID

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.slug_port import ISlugService
from app.domains.nodes.infrastructure.models.node import Node


class SlugService(ISlugService):
    """Default slug service using sha256-short ids scoped per author."""

    _LEN: Final[int] = 16

    async def unique_slug(
        self, db: AsyncSession, base: str, author_id: UUID, *, skip_node_id: int | None = None
    ) -> str:
        slug_base = slugify(base) or "node"
        idx = 0
        while True:
            text = slug_base if idx == 0 else f"{slug_base}-{idx}"
            candidate = hashlib.sha256(text.encode()).hexdigest()[: self._LEN]
            stmt = select(Node).where(Node.slug == candidate, Node.author_id == author_id)
            if skip_node_id is not None:
                stmt = stmt.where(Node.id != skip_node_id)
            res = await db.execute(stmt)
            if res.scalar_one_or_none() is None:
                return candidate
            idx += 1


__all__ = ["SlugService"]

