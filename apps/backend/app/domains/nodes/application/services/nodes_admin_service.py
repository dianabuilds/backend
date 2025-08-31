from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository


class NodesAdminService:
    def __init__(self, repo: INodeRepository) -> None:
        self._repo = repo

    async def list_by_author(
        self, author_id: UUID, workspace_id: UUID, limit: int = 50, offset: int = 0
    ) -> list:
        return await self._repo.list_by_author(author_id, workspace_id, limit, offset)

    async def bulk_set_visibility(
        self,
        db: AsyncSession,
        node_ids: list[UUID],
        is_visible: bool,
        workspace_id: UUID,
    ) -> int:
        count = await self._repo.bulk_set_visibility(node_ids, is_visible, workspace_id)
        await db.commit()
        return count
