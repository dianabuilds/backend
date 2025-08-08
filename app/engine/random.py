from __future__ import annotations

import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Sequence

from app.models.node import Node


async def get_random_node(
    db: AsyncSession,
    exclude_node_id: str | None = None,
    tag_whitelist: Sequence[str] | None = None,
) -> Node | None:
    query = select(Node).where(Node.is_visible == True, Node.is_public == True)
    if exclude_node_id:
        query = query.where(Node.id != exclude_node_id)
    result = await db.execute(query)
    nodes = result.scalars().all()
    if tag_whitelist:
        whitelist = set(tag_whitelist)
        nodes = [n for n in nodes if {t.slug for t in n.tags} & whitelist]
    if not nodes:
        return None
    return random.choice(nodes)
