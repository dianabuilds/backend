from __future__ import annotations

from domains.platform.events.adapters.event_bus_memory import (
    InMemoryEventBus,
)
from domains.platform.events.adapters.outbox_memory import MemoryOutbox
from domains.platform.events.service import Events
from domains.platform.notifications.logic.dispatcher import (
    register_channel,
)
from domains.platform.notifications.wires import register_event_relays


def test_notifications_register_event_relays_and_dispatch():
    # Arrange events bus and capture channel
    bus = InMemoryEventBus()
    outbox = MemoryOutbox()
    events = Events(outbox=outbox, bus=bus)
    captured: list[dict] = []
    register_channel("log", lambda payload: captured.append(dict(payload)))

    # Subscribe relay and emit
    register_event_relays(events, ["profile.updated.v1"])
    payload = {"id": "u1", "username": "Neo"}
    bus.emit("profile.updated.v1", payload)

    assert captured and captured[0]["id"] == "u1"
