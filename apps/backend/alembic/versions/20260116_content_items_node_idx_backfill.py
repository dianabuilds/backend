from __future__ import annotations

import asyncio
import logging

from alembic import op
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: F401

revision = "20260116_content_items_node_idx_backfill"
down_revision = "20260115_content_items_bigint_ids"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


async def _scan_and_backfill() -> None:
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine) as session:
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
            else:
                logger.warning(
                    "workspace mismatch for node %s: node_ws=%s, item_ws=%s",
                    node.id,
                    node.workspace_id,
                    item.workspace_id,
                )
        await session.commit()
    await engine.dispose()


def upgrade() -> None:
    asyncio.run(_scan_and_backfill())
    op.execute("COMMIT")
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS content_items_node_id_idx ON content_items (node_id);"
    )
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS content_items_workspace_slug_idx ON content_items (workspace_id, slug);"
    )
    op.execute("BEGIN")


def downgrade() -> None:
    op.execute("COMMIT")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS content_items_node_id_idx;")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS content_items_workspace_slug_idx;")
    op.execute("BEGIN")
