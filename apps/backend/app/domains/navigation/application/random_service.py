from __future__ import annotations

import random
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.preview import PreviewContext
from app.domains.navigation.application.access_policy import has_access_async
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User


class RandomService:
    async def get_random_node(
        self,
        db: AsyncSession,
        user: User | None = None,
        exclude_node_id: str | None = None,
        tag_whitelist: Sequence[str] | None = None,
        preview: PreviewContext | None = None,
    ) -> Node | None:
        if preview and preview.seed is not None:
            random.seed(preview.seed)
        query = select(Node).where(
            Node.is_visible,
            Node.is_public,
            Node.is_recommendable,
        )
        if exclude_node_id:
            query = query.where(Node.id != exclude_node_id)
        result = await db.execute(query)
        nodes = result.scalars().all()
        if tag_whitelist:
            whitelist = set(tag_whitelist)
            nodes = [n for n in nodes if {t.slug for t in n.tags} & whitelist]
        nodes = [n for n in nodes if await has_access_async(n, user, preview)]
        if not nodes:
            return None
        return random.choice(nodes)
