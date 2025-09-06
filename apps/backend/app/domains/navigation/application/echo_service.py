from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.navigation.application.access_policy import has_access_async
from app.domains.navigation.infrastructure.models.echo_models import EchoTrace
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from app.domains.users.infrastructure.models.user import User


class EchoService:
    async def record_echo_trace(
        self,
        db: AsyncSession,
        from_node: Node,
        to_node: Node,
        user: User | None,
        *,
        source: str | None = None,
        channel: str | None = None,
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
        user: User | None = None,
        preview: PreviewContext | None = None,
        space_id: int | None = None,
    ) -> list[Node]:
        if space_id is None:
            space_id = getattr(node, "workspace_id", getattr(node, "account_id", None))
        stmt = select(NavigationCache.echo).where(NavigationCache.node_slug == node.slug)
        if space_id is not None:
            stmt = stmt.where(NavigationCache.space_id == space_id)
        result = await db.execute(stmt)
        slugs = result.scalar_one_or_none() or []
        ordered_nodes: list[Node] = []
        for slug in slugs[:limit]:
            if space_id is not None:
                if hasattr(Node, "workspace_id"):
                    node_query = select(Node).where(
                        Node.slug == slug, Node.workspace_id == space_id
                    )
                else:
                    node_query = select(Node).where(
                        Node.slug == slug,
                        Node.account_id == space_id,
                    )
            else:
                node_query = select(Node).where(Node.slug == slug)
            res = await db.execute(node_query)
            n = res.scalar_one_or_none()
            if n and await has_access_async(n, user, preview):
                ordered_nodes.append(n)
        return ordered_nodes
