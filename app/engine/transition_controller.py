from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.random import get_random_node
from app.engine.compass import get_compass_nodes
from app.engine.echo import get_echo_transitions
from app.models.node import Node
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
        nodes = await get_compass_nodes(db, node, user, max_options)
        return [
            TransitionOption(slug=n.slug, label=n.title, mode=mode.mode)
            for n in nodes
        ]
    if mode.mode == "echo":
        nodes = await get_echo_transitions(db, node, max_options, user=user)
        return [
            TransitionOption(slug=n.slug, label=n.title, mode=mode.mode)
            for n in nodes
        ]
    if mode.mode == "random":
        options: List[TransitionOption] = []
        whitelist = None
        if mode.filters:
            whitelist = mode.filters.get("tag_whitelist")
        for _ in range(max_options):
            rnd = await get_random_node(
                db,
                user=user,
                exclude_node_id=node.id,
                tag_whitelist=whitelist,
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
