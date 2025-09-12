from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.navigation_service import NavigationService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.application.ports.cache_port import INodeCacheInvalidation
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.telemetry.log_events import cache_invalidate


class NodeCacheInvalidation(INodeCacheInvalidation):
    def __init__(self) -> None:
        self._navcache = NavigationCacheService(CoreCacheAdapter())
        self._navsvc = NavigationService()

    async def invalidate_for_node(self, db: AsyncSession, node: Node) -> None:
        await self._navsvc.invalidate_navigation_cache(db, node)
        cache_invalidate("nav", reason="node_update", key=node.slug)
        cache_invalidate("navm", reason="node_update", key=node.slug)
        cache_invalidate("comp", reason="node_update")

    async def invalidate_by_user(self, user_id):  # type: ignore[override]
        await self._navcache.invalidate_navigation_by_user(user_id)

    async def invalidate_compass_by_user(self, user_id):  # type: ignore[override]
        await self._navcache.invalidate_compass_by_user(user_id)


__all__ = ["NodeCacheInvalidation"]


