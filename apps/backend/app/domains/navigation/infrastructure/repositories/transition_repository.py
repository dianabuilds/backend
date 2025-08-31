from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
    NodeTransitionType,
)
from app.schemas.transition import NodeTransitionCreate


class TransitionRepository:
    """Data access for NodeTransition."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, transition_id: UUID) -> NodeTransition | None:
        return await self.session.get(NodeTransition, transition_id)

    async def delete(self, transition: NodeTransition) -> None:
        await self.session.delete(transition)
        await self.session.commit()

    async def create(
        self,
        from_node_id: UUID,
        to_node_id: UUID,
        payload: NodeTransitionCreate,
        user_id: UUID,
    ) -> NodeTransition:
        transition = NodeTransition(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            type=NodeTransitionType(payload.type),
            condition=(
                payload.condition.model_dump(exclude_none=True)
                if payload.condition
                else {}
            ),
            weight=payload.weight,
            label=payload.label,
            created_by=user_id,
        )
        self.session.add(transition)
        await self.session.commit()
        await self.session.refresh(transition)
        return transition
