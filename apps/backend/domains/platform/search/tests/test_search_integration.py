from __future__ import annotations

import asyncio

import fakeredis
import pytest

from domains.platform.events.adapters.event_bus_redis import (
    RedisEventBus,
)
from domains.platform.events.adapters.outbox_redis import RedisOutbox
from domains.platform.events.application.publisher import Events
from domains.platform.search.ports import Doc
from domains.platform.search.wires import (
    build_container,
    register_event_indexers,
)


@pytest.mark.asyncio
async def test_search_upsert_and_query():
    c = build_container()
    await c.service.upsert(Doc(id="d1", title="Neo", text="The One", tags=("profile",)))
    hits = await c.service.search("neo", tags=None, match="any", limit=10, offset=0)
    assert hits and hits[0].id == "d1"


@pytest.mark.asyncio
async def test_event_indexing_profile_updated():
    c = build_container()
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    bus = RedisEventBus(
        redis_url="redis://fake-host/0",
        topics=["profile.updated.v1"],
        group="test",
        redis_client=fake,
    )
    outbox = RedisOutbox("redis://fake-host/0", redis_client=fake)
    events = Events(outbox=outbox, bus=bus)
    register_event_indexers(events, c)

    payload = {"id": "u42", "username": "Trinity"}
    handler = bus._routes["profile.updated.v1"]
    handler("profile.updated.v1", payload)
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    hits = await c.service.search("Trinity", tags=None, match="any", limit=10, offset=0)
    assert any(h.id == "profile:u42" for h in hits)
