from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any, cast

from domains.platform.events.application.publisher import Events
from domains.product.nodes.application.service import NodeService

logger = logging.getLogger("nodes.embedding.worker")


async def _process(service: NodeService, payload: dict[str, Any]) -> None:
    node_id = payload.get("id")
    if node_id is None:
        return
    try:
        await cast(
            Awaitable[Any],
            service.recompute_embedding(
                int(node_id), reason=str(payload.get("reason") or "worker")
            ),
        )
    except Exception:
        logger.exception("embedding_job_failed", extra={"node_id": node_id})


def register_embedding_worker(events: Events, service: NodeService) -> None:
    """Subscribe embedding recompute handler to the events bus."""

    async def _handler(_topic: str, payload: dict[str, Any]) -> None:
        await _process(service, payload)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:

        def _sync_handler(topic: str, payload: dict[str, Any]) -> None:
            asyncio.run(_handler(topic, payload))

        events.on("node.embedding.requested.v1", _sync_handler)
    else:

        def _schedule(topic: str, payload: dict[str, Any]) -> None:
            loop.create_task(_handler(topic, payload))

        events.on("node.embedding.requested.v1", _schedule)


__all__ = ["register_embedding_worker"]
