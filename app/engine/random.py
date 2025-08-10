from __future__ import annotations

import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Sequence

from app.models.node import Node
from app.models.user import User
from .filters import has_access


async def get_random_node(
    db: AsyncSession,
    user: User | None = None,
    exclude_node_id: str | None = None,
    tag_whitelist: Sequence[str] | None = None,
) -> Node | None:
    """Return a random accessible node.

    The same visibility and premium filters are applied here as for other
    navigation sources.
    """

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
    nodes = [n for n in nodes if has_access(n, user)]
    if not nodes:
        return None
    return random.choice(nodes)
