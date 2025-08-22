from __future__ import annotations

import random
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.navigation.application.access_policy import has_access_async


class RandomService:
    async def get_random_node(
        self,
        db: AsyncSession,
        user: User | None = None,
        exclude_node_id: str | None = None,
        tag_whitelist: Sequence[str] | None = None,
    ) -> Node | None:
        query = select(Node).where(
            Node.is_visible == True,  # noqa: E712
            Node.is_public == True,
            Node.is_recommendable == True,
        )
        if exclude_node_id:
            query = query.where(Node.id != exclude_node_id)
        result = await db.execute(query)
        nodes = result.scalars().all()
        if tag_whitelist:
            whitelist = set(tag_whitelist)
            nodes = [n for n in nodes if {t.slug for t in n.tags} & whitelist]
        nodes = [n for n in nodes if await has_access_async(n, user)]
        if not nodes:
            return None
        return random.choice(nodes)
