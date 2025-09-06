"""Reconcile NavigationCache space IDs.

This script ensures that ``NavigationCache`` rows have a ``space_id``
matching the owning node's workspace. Missing ``space_id`` values are
backfilled and mismatches are logged as anomalies.
"""

from __future__ import annotations

import asyncio
import logging

from apps.backend.app.core.config import settings
from apps.backend.app.core.logging_configuration import configure_logging
from apps.backend.app.domains.nodes.infrastructure.models.node import Node
from apps.backend.app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

logger = logging.getLogger("scripts.reconcile_spaces")


async def _reconcile() -> int:
    engine = create_async_engine(settings.database_url)
    anomaly_count = 0
    async with AsyncSession(engine, expire_on_commit=False) as session:
        stmt = select(NavigationCache, Node.workspace_id).join(
            Node, Node.slug == NavigationCache.node_slug
        )
        result = await session.execute(stmt)
        for cache, node_ws in result.all():
            if cache.space_id is None:
                cache.space_id = node_ws
                logger.info(
                    "backfilled_space_id",
                    extra={"cache_id": str(cache.id), "space_id": str(node_ws)},
                )
            elif cache.space_id != node_ws:
                anomaly_count += 1
                logger.warning(
                    "workspace_mismatch",
                    extra={
                        "cache_id": str(cache.id),
                        "cache_space": str(cache.space_id),
                        "node_workspace": str(node_ws),
                    },
                )
        await session.commit()
    await engine.dispose()
    return anomaly_count


def main() -> int:
    configure_logging(fmt="json")
    anomalies = asyncio.run(_reconcile())
    if anomalies:
        logger.error("anomalies_detected", extra={"count": anomalies})
    return 1 if anomalies else 0


if __name__ == "__main__":
    raise SystemExit(main())
