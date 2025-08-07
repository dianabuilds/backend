from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.transition import NodeTransition, NodeTransitionType
from app.models.node import Node
from app.models.user import User
from app.deps.guards import check_transition


async def get_transitions(
    db: AsyncSession,
    node: Node,
    user: User,
    transition_type: Optional[NodeTransitionType] = None,
) -> List[NodeTransition]:
    """Return transitions from a node that the user is allowed to see."""
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
