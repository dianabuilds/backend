from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository


class NodesAdminService:
    def __init__(self, repo: INodeRepository) -> None:
        self._repo = repo

    async def list_by_author(self, author_id: UUID, limit: int = 50, offset: int = 0) -> List:
        return await self._repo.list_by_author(author_id, limit, offset)

    async def bulk_set_visibility(self, db: AsyncSession, node_ids: List[UUID], is_visible: bool) -> int:
        count = await self._repo.bulk_set_visibility(node_ids, is_visible)
        await db.commit()
        return count

    async def bulk_set_tags(self, db: AsyncSession, node_ids: List[UUID], tags: list[str]) -> int:
        count = await self._repo.bulk_set_tags(node_ids, tags)
        await db.commit()
        return count

    async def bulk_set_tags_diff(self, db: AsyncSession, node_ids: List[UUID], add: list[str], remove: list[str]) -> int:
        count = await self._repo.bulk_set_tags_diff(node_ids, add, remove)
        await db.commit()
        return count

    async def bulk_set_public(self, db: AsyncSession, node_ids: List[UUID], is_public: bool) -> int:
        count = await self._repo.bulk_set_public(node_ids, is_public)
        await db.commit()
        return count
