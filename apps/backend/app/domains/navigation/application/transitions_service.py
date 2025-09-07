from __future__ import annotations

import logging
from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps.guards import check_transition
from app.core.preview import PreviewContext
from app.domains.admin.application.feature_flag_service import (
    FeatureFlagKey,
    get_effective_flags,
)
from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
    NodeTransitionType,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)


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
            .where(NodeTransition.from_node_id == node.id)
        )
        if transition_type is not None:
            query = query.where(NodeTransition.type == transition_type)
        result = await db.execute(query)
        transitions: Iterable[NodeTransition] = result.scalars().all()
        allowed: list[NodeTransition] = []
        for t in transitions:
            if await check_transition(t, user, preview):
                allowed.append(t)

        flags = await get_effective_flags(db, None, user)
        enabled = FeatureFlagKey.WEIGHTED_MANUAL_TRANSITIONS.value in flags
        is_shadow = bool(preview and preview.mode == "shadow")

        if enabled:
            before_ids = [t.id for t in allowed]
            allowed = sorted(allowed, key=lambda t: (-(t.weight or 0), t.created_at))
            if is_shadow:
                logger.info(
                    "weighted_manual_transitions.sort",
                    extra={"before": before_ids, "after": [t.id for t in allowed]},
                )
            return allowed

        if is_shadow:
            before_ids = [t.id for t in allowed]
            shadow_sorted = sorted(allowed, key=lambda t: (-(t.weight or 0), t.created_at))
            logger.info(
                "weighted_manual_transitions.shadow",
                extra={"before": before_ids, "after": [t.id for t in shadow_sorted]},
            )

        return allowed
