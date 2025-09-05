from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps.guards import check_transition
from app.core.preview import PreviewContext
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
    NodeTransitionType,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User


class TransitionsService:
    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: User,
        account_id: int,
        transition_type: NodeTransitionType | None = None,
        preview: PreviewContext | None = None,
    ) -> list[NodeTransition]:
        query = (
            select(NodeTransition)
            .join(Node, NodeTransition.to_node_id == Node.id)
            .where(
                NodeTransition.from_node_id == node.id,
                Node.account_id == account_id,
            )
        )
        if transition_type is not None:
            query = query.where(NodeTransition.type == transition_type)
        result = await db.execute(query)
        transitions: Iterable[NodeTransition] = result.scalars().all()
        allowed: list[NodeTransition] = []
        for t in transitions:
            if await check_transition(t, user, preview):
                allowed.append(t)
        return allowed
