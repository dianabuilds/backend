from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
)
from app.domains.nodes.infrastructure.models.node import Node


class NavigationStatsService:
    async def get_nodes_without_outgoing_pct(self, db: AsyncSession) -> float:
        total_nodes = (
            await db.execute(select(func.count()).select_from(Node))
        ).scalar() or 0
        if total_nodes == 0:
            return 0.0
        nodes_with_outgoing = (
            await db.execute(
                select(func.count(func.distinct(NodeTransition.from_node_id)))
            )
        ).scalar() or 0
        without_outgoing = total_nodes - nodes_with_outgoing
        return without_outgoing / total_nodes * 100
