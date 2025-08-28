# Script to migrate legacy quest data from content_items.quest_data
# Processes content_items of type "quest" and creates Quest domain objects
# using services from nodes and quests domains.

import asyncio
import logging
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure project root on sys.path
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from apps.backend.app.core.db.session import db_session  # type: ignore  # noqa: E402
from apps.backend.app.domains.nodes.application.node_service import NodeService  # type: ignore  # noqa: E402
from apps.backend.app.schemas.nodes_common import NodeType  # type: ignore  # noqa: E402
from apps.backend.app.domains.quests.authoring import (  # type: ignore  # noqa: E402
    batch_upsert_graph,
    create_quest,
)
from apps.backend.app.domains.quests.versions import create_version  # type: ignore  # noqa: E402
from apps.backend.app.domains.quests.schemas.quest import QuestCreate  # type: ignore  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def _load_legacy_quests(session: AsyncSession) -> List[Dict[str, Any]]:
    """Return raw rows for content_items with type='quest'."""
    sql = sa.text(
        "SELECT id, workspace_id, title, created_by_user_id, quest_data "
        "FROM content_items WHERE type = :t"
    )
    res = await session.execute(sql, {"t": "quest"})
    return [dict(r) for r in res.mappings().all()]


async def _migrate_one(session: AsyncSession, row: Dict[str, Any]) -> None:
    data = row.get("quest_data") or {}
    author_id: UUID | None = row.get("created_by_user_id")
    if not author_id:
        logger.warning("quest %s skipped: missing author", row.get("id"))
        return

    payload = QuestCreate(
        title=row.get("title") or "Untitled quest",
        subtitle=data.get("subtitle"),
        description=data.get("description"),
        cover_image=data.get("cover_image"),
        tags=data.get("tags") or [],
        price=data.get("price"),
        is_premium_only=data.get("is_premium_only", False),
        entry_node_id=data.get("entry_node_id"),
        nodes=data.get("nodes") or [],
        custom_transitions=data.get("custom_transitions"),
        allow_comments=data.get("allow_comments", True),
        structure=data.get("structure"),
        length=data.get("length"),
        tone=data.get("tone"),
        genre=data.get("genre"),
        locale=data.get("locale"),
        cost_generation=data.get("cost_generation"),
    )

    author = SimpleNamespace(id=author_id)
    quest = await create_quest(
        session,
        payload=payload,
        author=author,
        workspace_id=row.get("workspace_id"),
    )

    version = await create_version(
        session,
        quest_id=quest.id,
        created_by=author_id,
    )

    node_service = NodeService(session)
    nodes_spec: List[Dict[str, Any]] = []
    missing_nodes: List[str] = []
    node_ids: List[UUID] = data.get("nodes") or []
    for nid in node_ids:
        try:
            node = await node_service.get(row["workspace_id"], NodeType.article, nid)
            nodes_spec.append(
                {
                    "key": str(nid),
                    "title": node.title,
                    "type": "content",
                    "nodes": {"content_id": str(nid)},
                }
            )
        except Exception:
            missing_nodes.append(str(nid))
    if missing_nodes:
        logger.warning(
            "quest %s references missing content nodes: %s",
            row.get("id"),
            ", ".join(missing_nodes),
        )

    edges_spec: List[Dict[str, Any]] = []
    transitions: Dict[str, Any] = data.get("custom_transitions") or {}
    existing_keys = {n["key"] for n in nodes_spec}
    for from_id, targets in transitions.items():
        if str(from_id) not in existing_keys:
            logger.warning(
                "quest %s transition from missing node %s", row.get("id"), from_id
            )
            continue
        if not isinstance(targets, dict):
            logger.warning(
                "quest %s invalid transitions format for %s", row.get("id"), from_id
            )
            continue
        for to_id, meta in targets.items():
            if str(to_id) not in existing_keys:
                logger.warning(
                    "quest %s transition %s->%s refers to missing node",
                    row.get("id"),
                    from_id,
                    to_id,
                )
                continue
            label = meta.get("label") if isinstance(meta, dict) else None
            condition = meta.get("condition") if isinstance(meta, dict) else None
            edges_spec.append(
                {
                    "from_node_key": str(from_id),
                    "to_node_key": str(to_id),
                    "label": label,
                    "condition": condition,
                }
            )

    if nodes_spec:
        await batch_upsert_graph(
            session,
            version_id=version.id,
            nodes=nodes_spec,
            edges=edges_spec,
            remove_missing=False,
        )
    await session.commit()
    logger.info("quest %s migrated", row.get("id"))


async def migrate() -> None:
    async with db_session() as session:  # type: ignore
        rows = await _load_legacy_quests(session)
        for row in rows:
            try:
                await _migrate_one(session, row)
            except Exception:
                logger.exception("failed to migrate quest %s", row.get("id"))


if __name__ == "__main__":
    asyncio.run(migrate())
