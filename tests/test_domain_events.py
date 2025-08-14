import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.node import Node
from app.models.user import User
from app.services.events import NodeUpdated, get_event_bus
from app.services.navcache import navcache
from app.services.events import handlers as event_handlers
from contextlib import asynccontextmanager


@pytest.mark.asyncio
async def test_node_created_triggers_embedding_and_cache(client: AsyncClient, db_session, auth_headers):
    called = {"comp": 0}

    async def fake_compass_all():
        called["comp"] += 1

    monkey = pytest.MonkeyPatch()
    monkey.setattr(navcache, "invalidate_compass_all", fake_compass_all)

    @asynccontextmanager
    async def _cm():
        yield db_session

    monkey.setattr(event_handlers, "db_session", _cm)

    resp = await client.post(
        "/nodes",
        json={"title": "n1", "content": {}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    slug = resp.json()["slug"]
    res = await db_session.execute(select(Node).where(Node.slug == slug))
    node = res.scalars().first()
    assert node is not None
    await db_session.refresh(node)
    assert node.embedding_vector is not None
    assert called["comp"] == 1
    monkey.undo()


@pytest.mark.asyncio
async def test_idempotent_processing(db_session, test_user: User):
    node = Node(title="n", content={}, author_id=test_user.id)
    db_session.add(node)
    await db_session.commit()
    await db_session.refresh(node)

    called = {"nav": 0}

    async def fake_nav(slug: str) -> None:
        called["nav"] += 1

    monkey = pytest.MonkeyPatch()
    monkey.setattr(navcache, "invalidate_navigation_by_node", fake_nav)

    @asynccontextmanager
    async def _cm():
        yield db_session

    monkey.setattr(event_handlers, "db_session", _cm)

    event = NodeUpdated(
        node_id=node.id,
        slug=node.slug,
        author_id=test_user.id,
        tags_changed=True,
    )
    bus = get_event_bus()
    await bus.publish(event)
    await bus.publish(event)  # same event twice

    assert called["nav"] == 1
    monkey.undo()


@pytest.mark.asyncio
async def test_handler_retries(db_session, test_user: User):
    node = Node(title="n", content={}, author_id=test_user.id)
    db_session.add(node)
    await db_session.commit()
    await db_session.refresh(node)

    attempts = {"count": 0}

    async def failing_update(*args, **kwargs):
        attempts["count"] += 1
        raise RuntimeError("boom")

    monkey = pytest.MonkeyPatch()
    from app.engine import embedding

    monkey.setattr(event_handlers, "update_node_embedding", failing_update)

    @asynccontextmanager
    async def _cm():
        yield db_session

    monkey.setattr(event_handlers, "db_session", _cm)

    bus = get_event_bus()
    event = NodeUpdated(node_id=node.id, slug=node.slug, author_id=test_user.id)
    await bus.publish(event)
    # Handler should retry 3 times (max_retries)
    assert attempts["count"] == 3
    monkey.undo()
