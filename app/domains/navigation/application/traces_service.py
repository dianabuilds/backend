from __future__ import annotations

import random

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTrace, NodeTraceKind, NodeTraceVisibility
from app.domains.users.infrastructure.models.user import User


class TracesService:
    async def maybe_add_auto_trace(
        self, db: AsyncSession, node: Node, user: User, chance: float = 0.3
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
