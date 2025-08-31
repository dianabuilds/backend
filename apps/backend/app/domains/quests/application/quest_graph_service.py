from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.application.cache_singleton import navcache
from app.domains.quests.infrastructure.models.navigation_cache_models import NavigationCache
from app.domains.quests.infrastructure.models.quest_version_models import (
    QuestGraphEdge,
    QuestGraphNode,
    QuestVersion,
)
from app.domains.quests.schemas import QuestStep, QuestTransition


class QuestGraphService:
    """Service responsible for persistence of quest graphs and related cache."""

    async def load_graph(
        self, db: AsyncSession, version_id: UUID
    ) -> tuple[QuestVersion, List[QuestStep], List[QuestTransition]]:
        """Load quest graph for the given version."""
        version = await db.get(QuestVersion, version_id)
        if not version:
            raise ValueError("version_not_found")

        nodes: Iterable[QuestGraphNode] = (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        ).scalars().all()
        edges: Iterable[QuestGraphEdge] = (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        ).scalars().all()

        steps = [
            QuestStep(
                key=n.key,
                title=n.title,
                type=n.type,
            )
            for n in nodes
        ]
        transitions = [
            QuestTransition(
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
            for e in edges
        ]
        return version, steps, transitions

    async def save_graph(
        self,
        db: AsyncSession,
        version_id: UUID,
        steps: List[QuestStep],
        transitions: List[QuestTransition],
    ) -> None:
        """Persist quest graph and regenerate navigation cache."""
        await db.execute(
            delete(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
        )
        await db.execute(
            delete(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
        )
        await db.flush()

        for s in steps:
            db.add(
                QuestGraphNode(
                    version_id=version_id,
                    key=s.key,
                    title=s.title,
                    type=s.type,
                )
            )
        for t in transitions:
            db.add(
                QuestGraphEdge(
                    version_id=version_id,
                    from_node_key=t.from_node_key,
                    to_node_key=t.to_node_key,
                    label=t.label,
                    condition=t.condition,
                )
            )
        await db.flush()
        await self.invalidate_navigation_cache(db)
        await self.generate_navigation_cache(db, version_id)

    async def invalidate_navigation_cache(self, db: AsyncSession) -> None:
        """Remove all navigation cache rows."""
        await db.execute(delete(NavigationCache))
        await db.flush()
        try:
            await navcache.invalidate_navigation_all()
            await navcache.invalidate_compass_all()
        except Exception:
            pass

    async def generate_navigation_cache(
        self, db: AsyncSession, version_id: UUID
    ) -> None:
        """Generate navigation cache entries from stored graph."""
        _version, steps, transitions = await self.load_graph(db, version_id)
        await db.execute(delete(NavigationCache))
        adj: Dict[str, List[str]] = {}
        for t in transitions:
            adj.setdefault(t.from_node_key, []).append(t.to_node_key)
        now = datetime.utcnow().isoformat()
        for s in steps:
            data = {
                "mode": "auto",
                "transitions": [
                    {"slug": dst, "title": dst, "source_type": "cached"}
                    for dst in adj.get(s.key, [])
                ],
                "generated_at": now,
            }
            db.add(
                NavigationCache(
                    node_slug=s.key,
                    navigation=data,
                    compass=[],
                    echo=[],
                )
            )
        await db.flush()
