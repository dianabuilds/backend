from __future__ import annotations

import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node
from app.models.node_trace import NodeTrace, NodeTraceKind, NodeTraceVisibility
from app.models.user import User


async def maybe_add_auto_trace(
    db: AsyncSession, node: Node, user: User, chance: float = 0.3
) -> None:
    if random.random() < chance:
        trace = NodeTrace(
            node_id=node.id,
            user_id=user.id,
            kind=NodeTraceKind.auto,
            visibility=NodeTraceVisibility.public,
        )
        db.add(trace)
        await db.commit()
