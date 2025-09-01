# mypy: ignore-errors
# ruff: noqa: E402
from __future__ import annotations

"""Reconcile node and content item records.

This script scans for ``Node`` records missing a related ``NodeItem``
and backfills them using :class:`NodeService`. Workspace mismatches
are logged as anomalies and trigger a non-zero exit code.
"""

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.app.core.config import settings  # noqa: E402
from apps.backend.app.core.logging_configuration import configure_logging  # noqa: E402
from apps.backend.app.domains.nodes.application.node_service import (
    NodeService,  # noqa: E402
)
from apps.backend.app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from apps.backend.app.domains.nodes.models import NodeItem  # noqa: E402

logger = logging.getLogger("scripts.reconcile_node_items")


async def _reconcile() -> int:
    engine = create_async_engine(settings.database_url)
    anomaly_count = 0
    async with AsyncSession(engine, expire_on_commit=False) as session:
        service = NodeService(session)
        stmt = (
            select(Node, NodeItem)
            .outerjoin(NodeItem, Node.id == NodeItem.node_id)
            .where(
                or_(
                    NodeItem.node_id.is_(None),
                    Node.workspace_id != NodeItem.workspace_id,
                )
            )
        )
        result = await session.execute(stmt)
        for node, item in result.all():
            if item is None:
                await service.create_item_for_node(node)
                logger.info(
                    "backfilled_node_item",
                    extra={"node_id": node.id, "workspace_id": str(node.workspace_id)},
                )
            else:
                anomaly_count += 1
                logger.warning(
                    "workspace_mismatch",
                    extra={
                        "node_id": node.id,
                        "node_workspace": str(node.workspace_id),
                        "item_workspace": str(item.workspace_id),
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
