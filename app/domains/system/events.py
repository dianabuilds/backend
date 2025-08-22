from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Set
from uuid import UUID, uuid4

from app.domains.navigation.application.cache_singleton import navcache


@dataclass(frozen=True)
class ContentPublished:
    content_id: UUID
    slug: str
    author_id: UUID
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class ContentUpdated:
    content_id: UUID
    slug: str
    author_id: UUID
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class ContentArchived:
    content_id: UUID
    slug: str
    author_id: UUID
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class NodeCreated:
    node_id: UUID
    slug: str
    author_id: UUID
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(frozen=True)
class NodeUpdated:
    node_id: UUID
    slug: str
    author_id: UUID
    tags_changed: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[type, List[Callable[[Any], Awaitable[None]]]] = {}
        self._processed: Set[str] = set()

    def subscribe(self, event_type: type, handler: Callable[[Any], Awaitable[None]]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Any) -> None:
        event_id = getattr(event, "id", None)
        if event_id is None:
            event_id = uuid4().hex
            setattr(event, "id", event_id)
        if event_id in self._processed:
            return
        self._processed.add(event_id)
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
                        break
                    await asyncio.sleep(0)


class _Handlers:
    def __init__(self) -> None:
        from app.core.db.session import db_session  # lazy to avoid cycles
        from app.domains.ai.application.embedding_service import update_node_embedding

        self.db_session = db_session
        self.update_node_embedding = update_node_embedding

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


handlers = _Handlers()
_bus = EventBus()
_registered = False


def register_handlers() -> None:
    global _registered
    if _registered:
        return
    _bus.subscribe(NodeCreated, handlers.handle_node_created)
    _bus.subscribe(NodeUpdated, handlers.handle_node_updated)
    _registered = True


def get_event_bus() -> EventBus:
    register_handlers()
    return _bus


__all__ = [
    "NodeCreated",
    "NodeUpdated",
    "ContentPublished",
    "ContentUpdated",
    "ContentArchived",
    "get_event_bus",
    "register_handlers",
    "handlers",
]

