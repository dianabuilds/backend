from __future__ import annotations

import asyncio

import pytest

from apps.backendDDD.domains.platform.events.adapters.event_bus_memory import (
    InMemoryEventBus,
)
from apps.backendDDD.domains.platform.events.adapters.outbox_memory import MemoryOutbox
from apps.backendDDD.domains.platform.events.service import Events
from apps.backendDDD.domains.platform.search.ports import Doc
from apps.backendDDD.domains.platform.search.wires import (
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
    # Arrange search container and events bus
    c = build_container()
    bus = InMemoryEventBus()
    outbox = MemoryOutbox()
    events = Events(outbox=outbox, bus=bus)
    register_event_indexers(events, c)

    # Emit an event and allow async handler to run
    payload = {"id": "u42", "username": "Trinity"}
    bus.emit("profile.updated.v1", payload)
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    # Verify indexed
    hits = await c.service.search("Trinity", tags=None, match="any", limit=10, offset=0)
    assert any(h.id == "profile:u42" for h in hits)
