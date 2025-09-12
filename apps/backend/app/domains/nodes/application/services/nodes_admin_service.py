from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository


class NodesAdminService:
    def __init__(self, repo: INodeRepository) -> None:
        self._repo = repo

    async def list_by_author(
        self, author_id: UUID, tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> list:
        # Repository interface is profile-centric and does not filter by tenant.
        # Tenant is accepted for consistency but not used at this layer.
        return await self._repo.list_by_author(author_id, limit=limit, offset=offset)

    async def bulk_set_visibility(
        self,
        db: AsyncSession,
        node_ids: list[int],
        is_visible: bool,
        tenant_id: UUID,
    ) -> int:
        # Repository method is tenant-agnostic; apply to provided nodes directly.
        count = await self._repo.bulk_set_visibility(node_ids, is_visible)
        await db.commit()
        return count
