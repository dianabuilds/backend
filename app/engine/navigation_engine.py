from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.compass import get_compass_nodes
from app.engine.echo import get_echo_transitions
from app.engine.random import get_random_node
from app.models.node import Node
from app.models.user import User
from app.services.navigation_cache import navigation_cache


async def generate_transitions(
    db: AsyncSession, node: Node, user: Optional[User]
) -> List[Dict[str, str]]:
    transitions: List[Dict[str, str]] = []
    compass_nodes = await get_compass_nodes(db, node, user, 1)
    if compass_nodes:
        transitions.append({"slug": compass_nodes[0].slug, "type": "compass"})
    echo_nodes = await get_echo_transitions(db, node, 1)
    if echo_nodes:
        transitions.append({"slug": echo_nodes[0].slug, "type": "echo"})
    rnd = await get_random_node(db, exclude_node_id=node.id)
    if rnd:
        transitions.append({"slug": rnd.slug, "type": "random"})
    return transitions


async def get_navigation(
    db: AsyncSession, node: Node, user: Optional[User]
) -> Dict[str, object]:
    user_key = str(user.id) if user else None
    cached = await navigation_cache.get(user_key, str(node.id))
    if cached:
        return cached
    transitions = await generate_transitions(db, node, user)
    data = {"transitions": transitions, "generated_at": datetime.utcnow().isoformat()}
    await navigation_cache.set(user_key, str(node.id), data)
    return data


async def invalidate_navigation_cache(user: Optional[User], node: Node) -> None:
    await navigation_cache.invalidate(str(user.id) if user else None, str(node.id))


async def invalidate_all_for_node(node: Node) -> None:
    await navigation_cache.invalidate_all_for_node(str(node.id))
