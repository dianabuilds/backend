from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.application.cache_singleton import navcache

from .models import NodeCreated, NodePublished, NodeUpdated


class _Handlers:
    def __init__(self) -> None:
        from app.domains.ai.application.embedding_service import (
            update_node_embedding,
        )
        from app.domains.search.service import index_content

        self.update_node_embedding: Callable[..., Awaitable[Any]] = (
            update_node_embedding
        )
        self.index_content: Callable[..., Awaitable[Any]] = index_content

        @asynccontextmanager
        async def _db_session() -> AsyncIterator[AsyncSession]:
            from app.core.db.session import db_session as real_db_session

            async with real_db_session() as session:
                yield session

        self.db_session = _db_session

    async def handle_node_created(self, event: NodeCreated) -> None:
        async with self.db_session() as session:
            await self.update_node_embedding(session, event.node_id)
        try:
            await navcache.invalidate_compass_all()
        except Exception:
            pass

    async def handle_node_updated(self, event: NodeUpdated) -> None:
        async with self.db_session() as session:
            await self.update_node_embedding(session, event.node_id)
        if event.tags_changed:
            try:
                await navcache.invalidate_navigation_by_node(event.slug)
            except Exception:
                pass
        try:
            await navcache.invalidate_compass_all()
        except Exception:
            pass

    async def handle_node_published(self, event: NodePublished) -> None:
        try:
            await self.index_content(event.node_id)
        except Exception:
            pass
        try:
            await navcache.invalidate_navigation_by_node(event.slug)
            await navcache.invalidate_modes_by_node(event.slug)
            await navcache.invalidate_compass_all()
        except Exception:
            pass


handlers = _Handlers()

__all__ = ["handlers"]
