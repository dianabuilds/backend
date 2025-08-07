from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.random import get_random_node
from app.engine.transitions import get_transitions
from app.models.node import Node
from app.models.transition import NodeTransitionType
from app.models.user import User
from app.schemas.transition import TransitionMode, TransitionOption


async def apply_mode(
    db: AsyncSession,
    node: Node,
    user: User,
    mode: TransitionMode,
    max_options: int,
) -> List[TransitionOption]:
    """Return transition options for a given mode."""
    if mode.mode == "compass":
        transitions = await get_transitions(db, node, user, NodeTransitionType.manual)
        transitions.sort(
            key=lambda t: len(set(node.tags or []) & set(t.to_node.tags or [])),
            reverse=True,
        )
        return [
            TransitionOption(slug=t.to_node.slug, label=t.label, mode=mode.mode)
            for t in transitions[:max_options]
        ]
    if mode.mode == "echo":
        transitions = await get_transitions(db, node, user)
        transitions.sort(
            key=lambda t: getattr(t.to_node, "updated_at", datetime.min),
            reverse=True,
        )
        return [
            TransitionOption(slug=t.to_node.slug, label=t.label, mode=mode.mode)
            for t in transitions[:max_options]
        ]
    if mode.mode == "random":
        options: List[TransitionOption] = []
        whitelist = None
        if mode.filters:
            whitelist = mode.filters.get("tag_whitelist")
        for _ in range(max_options):
            rnd = await get_random_node(
                db, exclude_node_id=node.id, tag_whitelist=whitelist
            )
            if not rnd:
                break
            if rnd.slug in {o.slug for o in options}:
                continue
            options.append(
                TransitionOption(slug=rnd.slug, label=rnd.title, mode=mode.mode)
            )
            if len(options) >= max_options:
                break
        return options
    return []
