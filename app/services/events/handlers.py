"""Event handlers for side effects."""
from __future__ import annotations

import logging
from typing import Callable

from app.core.log_events import cache_invalidate
from app.db.session import db_session
from app.engine.embedding import update_node_embedding
from app.models.node import Node
from app.services.navcache import navcache

from .events import NodeCreated, NodeUpdated
from .bus import get_event_bus

logger = logging.getLogger(__name__)


async def handle_embedding(event: NodeCreated | NodeUpdated) -> None:
    """Update embedding for a node."""
    async with db_session() as session:
        node = await session.get(Node, event.node_id)
        if node is None:
            logger.warning("Node %s not found for embedding", event.node_id)
            return
        await update_node_embedding(session, node)
        await session.commit()


async def handle_cache_invalidation(event: NodeCreated | NodeUpdated) -> None:
    """Invalidate cache for affected node."""
    if isinstance(event, NodeCreated):
        await navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="node_create")
    else:
        if event.tags_changed:
            await navcache.invalidate_navigation_by_node(event.slug)
            cache_invalidate("nav", reason="node_edit", key=event.slug)
        await navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="node_edit")


_registered = False


def register_handlers() -> None:
    """Register event handlers once."""
    global _registered
    if _registered:
        return
    bus = get_event_bus()
    bus.subscribe(NodeCreated, handle_embedding)
    bus.subscribe(NodeUpdated, handle_embedding)
    bus.subscribe(NodeCreated, handle_cache_invalidation)
    bus.subscribe(NodeUpdated, handle_cache_invalidation)
    _registered = True
