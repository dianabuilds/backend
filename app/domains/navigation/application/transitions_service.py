from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps.guards import check_transition
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTransition, NodeTransitionType
from app.domains.users.infrastructure.models.user import User


class TransitionsService:
    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: User,
        transition_type: Optional[NodeTransitionType] = None,
    ) -> List[NodeTransition]:
        query = select(NodeTransition).where(NodeTransition.from_node_id == node.id)
        if transition_type is not None:
            query = query.where(NodeTransition.type == transition_type)
        result = await db.execute(query)
        transitions: Iterable[NodeTransition] = result.scalars().all()
        allowed: List[NodeTransition] = []
        for t in transitions:
            if check_transition(t, user):
                allowed.append(t)
        return allowed
