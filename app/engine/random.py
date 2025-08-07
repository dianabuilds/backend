from __future__ import annotations

import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node


async def get_random_node(db: AsyncSession, exclude_node_id: str | None = None) -> Node | None:
    query = select(Node).where(Node.is_visible == True, Node.is_public == True)
    if exclude_node_id:
        query = query.where(Node.id != exclude_node_id)
    result = await db.execute(query)
    nodes = result.scalars().all()
    if not nodes:
        return None
    return random.choice(nodes)
