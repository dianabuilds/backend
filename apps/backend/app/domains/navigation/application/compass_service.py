from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.navigation.application.access_policy import has_access_async
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.limits import workspace_limit


class CompassService:
    def __init__(self) -> None:
        pass

    @workspace_limit("compass_calls", scope="day", amount=1)
    async def get_compass_nodes(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        limit: int = 5,
        preview: PreviewContext | None = None,
    ) -> list[Node]:
        result = await db.execute(
            select(NavigationCache.compass).where(
                NavigationCache.node_slug == node.slug
            )
        )
        slugs = result.scalar_one_or_none() or []
        nodes: list[Node] = []
        for slug in slugs[:limit]:
            res = await db.execute(select(Node).where(Node.slug == slug))
            n = res.scalar_one_or_none()
            if n and await has_access_async(n, user, preview):
                nodes.append(n)
        return nodes
