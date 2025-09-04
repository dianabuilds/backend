from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from app.domains.navigation.application.cache_singleton import navcache
from app.domains.telemetry.application.event_metrics_facade import event_metrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodePublished:
    node_id: int
    slug: str
    author_id: UUID
    workspace_id: UUID | None = None
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class NodeArchived:
    node_id: int
    slug: str
    author_id: UUID
    workspace_id: UUID | None = None
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class NodeCreated:
    node_id: int
    slug: str
    author_id: UUID
    workspace_id: UUID | None = None
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class NodeUpdated:
    node_id: int
    slug: str
    author_id: UUID
    workspace_id: UUID | None = None
    tags_changed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class AchievementUnlocked:
    achievement_id: UUID
    user_id: UUID
    workspace_id: UUID
    id: str = field(default_factory=lambda: uuid4().hex)


EVENT_METRIC_NAMES: dict[type, str] = {
    NodeCreated: "node.created",
    NodeUpdated: "node.updated",
    NodePublished: "node.publish",
    NodeArchived: "node.archived",
    AchievementUnlocked: "achievement",
}


async def _record_metric(event: Any) -> None:
    name = EVENT_METRIC_NAMES.get(type(event))
    if not name:
        return
    ws = getattr(event, "workspace_id", None)
    event_metrics.inc(name, str(ws) if ws is not None else None)


class EventBus:
    def __init__(self, processed_maxlen: int = 1024) -> None:
        self._handlers: dict[type, list[Callable[[Any], Awaitable[None]]]] = {}
        self._processed: deque[str] = deque()
        self._processed_set: set[str] = set()
        self._processed_maxlen = processed_maxlen

    def subscribe(
        self, event_type: type, handler: Callable[[Any], Awaitable[None]]
    ) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Any) -> None:
        event_id = getattr(event, "id", None)
        if event_id is None:
            event_id = uuid4().hex
            event.id = event_id
        if event_id in self._processed_set:
            return
        self._processed.append(event_id)
        self._processed_set.add(event_id)
        if len(self._processed) > self._processed_maxlen:
            old = self._processed.popleft()
            self._processed_set.discard(old)
        handlers = self._handlers.get(type(event), [])
        for h in handlers:
            attempts = 0
            while True:
                try:
                    await h(event)
                    break
                except Exception:
                    attempts += 1
                    if attempts >= 3:
                        logger.exception(
                            "event handler failed after %s attempts", attempts
                        )
                        break
                    await asyncio.sleep(0)


class _Handlers:
    def __init__(self) -> None:
        from app.domains.ai.application.embedding_service import (
            update_node_embedding,
        )
        from app.domains.search.service import index_content

        self.update_node_embedding = update_node_embedding
        self.index_content = index_content

        @asynccontextmanager
        async def _db_session():
            """Lazily import the real db_session to avoid circular imports."""
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
        """Index published node and invalidate caches."""
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
_bus = EventBus()
_registered = False


def register_handlers() -> None:
    global _registered
    if _registered:
        return
    for ev in EVENT_METRIC_NAMES:
        _bus.subscribe(ev, _record_metric)
    _bus.subscribe(NodeCreated, handlers.handle_node_created)
    _bus.subscribe(NodeUpdated, handlers.handle_node_updated)
    _bus.subscribe(NodePublished, handlers.handle_node_published)
    _registered = True


def get_event_bus() -> EventBus:
    register_handlers()
    return _bus


__all__ = [
    "NodeCreated",
    "NodeUpdated",
    "NodePublished",
    "NodeArchived",
    "AchievementUnlocked",
    "get_event_bus",
    "register_handlers",
    "handlers",
]
