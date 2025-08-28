from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)


class NavigationService:
    def __init__(self) -> None:
        pass

    async def generate_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        preview: PreviewContext | None = None,
    ) -> List[Dict[str, object]]:
        result = await db.execute(
            select(NavigationCache.navigation).where(
                NavigationCache.node_slug == node.slug
            )
        )
        data = result.scalar_one_or_none()
        if not data:
            return []
        return data.get("transitions", [])

    async def get_navigation(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        preview: PreviewContext | None = None,
    ) -> Dict[str, object]:
        result = await db.execute(
            select(NavigationCache.navigation).where(
                NavigationCache.node_slug == node.slug
            )
        )
        data = result.scalar_one_or_none()
        if data:
            return data
        return {
            "mode": "auto",
            "transitions": [],
            "generated_at": (
                preview.now if preview and preview.now else datetime.utcnow()
            ).isoformat(),
        }

    async def invalidate_navigation_cache(
        self, db: AsyncSession, node: Node
    ) -> None:
        await db.execute(
            delete(NavigationCache).where(NavigationCache.node_slug == node.slug)
        )
        await db.flush()
