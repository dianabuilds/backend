from __future__ import annotations

import fakeredis

from domains.platform.events.adapters.event_bus_redis import (
    RedisEventBus,
)
from domains.platform.events.adapters.outbox_redis import RedisOutbox
from domains.platform.events.service import Events
from domains.platform.notifications.logic.dispatcher import (
    register_channel,
)
from domains.platform.notifications.wires import register_event_relays


def test_notifications_register_event_relays_and_dispatch():
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    bus = RedisEventBus(
        redis_url="redis://fake-host/0",
        topics=["profile.updated.v1"],
        group="test",
        redis_client=fake,
    )
    outbox = RedisOutbox("redis://fake-host/0", redis_client=fake)
    events = Events(outbox=outbox, bus=bus)
    captured: list[dict] = []
    register_channel("log", lambda payload: captured.append(dict(payload)))

    register_event_relays(events, ["profile.updated.v1"])
    payload = {"id": "u1", "username": "Neo"}
    handler = bus._routes["profile.updated.v1"]
    handler("profile.updated.v1", payload)

    assert captured and captured[0]["id"] == "u1"
