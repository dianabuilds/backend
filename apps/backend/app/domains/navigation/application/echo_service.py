from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.infrastructure.models.echo_models import EchoTrace
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.navigation.application.access_policy import has_access_async
from app.core.preview import PreviewContext
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)


class EchoService:
    async def record_echo_trace(
        self,
        db: AsyncSession,
        from_node: Node,
        to_node: Node,
        user: Optional[User],
        *,
        source: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> None:
        trace = EchoTrace(
            from_node_id=from_node.id,
            to_node_id=to_node.id,
            user_id=user.id if user and user.is_premium else None,
            source=source,
            channel=channel,
        )
        db.add(trace)
        await db.commit()

    async def get_echo_transitions(
        self,
        db: AsyncSession,
        node: Node,
        limit: int = 3,
        *,
        user: Optional[User] = None,
        preview: PreviewContext | None = None,
    ) -> List[Node]:
        result = await db.execute(
            select(NavigationCache.echo).where(
                NavigationCache.node_slug == node.slug
            )
        )
        slugs = result.scalar_one_or_none() or []
        ordered_nodes: List[Node] = []
        for slug in slugs[:limit]:
            res = await db.execute(select(Node).where(Node.slug == slug))
            n = res.scalar_one_or_none()
            if n and await has_access_async(n, user, preview):
                ordered_nodes.append(n)
        return ordered_nodes
