from __future__ import annotations

import fakeredis
import pytest

from domains.platform.events.adapters.redis_bus import RedisBus
from domains.platform.flags.adapters.store_redis import RedisFlagStore
from domains.platform.flags.application.commands import (
    delete_flag,
    upsert_flag,
)
from domains.platform.flags.application.queries import (
    check_flag,
    list_flags,
)
from domains.platform.flags.application.service import FlagService
from domains.platform.flags.domain.models import Flag
from packages.core.redis_outbox import RedisOutboxCore


def test_redis_outbox_and_bus_roundtrip() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    bus = RedisBus("redis://localhost/0", client=client)
    outbox = RedisOutboxCore("redis://localhost/0", client=client)

    topic = "notifications.broadcast"
    group = "workers"

    bus.ensure_group(topic, group)
    message_id = outbox.publish(topic, {"event": "ping"}, key="broadcast:1")

    batch = bus.read_batch([topic], group, "consumer-1", count=10, block_ms=5)
    assert batch
    stream, entries = batch[0]
    assert stream == f"events:{topic}"
    entry_id, fields = entries[0]
    assert entry_id == message_id
    assert bus.to_payload(fields) == {"event": "ping"}

    assert bus.xlen(topic) >= 1
    assert bus.xpending(topic, group) >= 1

    bus.ack(topic, group, entry_id)
    assert bus.xpending(topic, group) == 0


@pytest.mark.asyncio
async def test_redis_flag_store_roundtrip() -> None:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    store = RedisFlagStore(client)

    flag = Flag(
        slug="beta",
        enabled=True,
        rollout=25,
        users={"user:1"},
        roles={"admin"},
        segments={"beta"},
        meta={"note": "integration"},
    )

    await store.upsert(flag)

    loaded = await store.get(flag.slug)
    assert loaded is not None
    assert loaded.slug == flag.slug
    assert loaded.users == flag.users
    assert loaded.roles == flag.roles
    assert loaded.segments == flag.segments
    assert loaded.meta == flag.meta

    items = await store.list()
    assert any(item.slug == flag.slug for item in items)

    await store.delete(flag.slug)
    assert await store.get(flag.slug) is None


@pytest.mark.asyncio
async def test_flag_commands_queries_with_redis_store() -> None:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    store = RedisFlagStore(client)
    service = FlagService(store)

    payload = {
        "slug": "feature-x",
        "description": "test flag",
        "status": "custom",
        "segments": ["beta"],
        "rollout": 20,
        "meta": {"owner": "qa"},
    }

    upserted = await upsert_flag(service, payload)
    assert upserted["flag"]["slug"] == "feature-x"
    assert upserted["flag"]["segments"] == ["beta"]
    assert upserted["flag"]["effective"] is False

    listed = await list_flags(service)
    assert listed["items"][0]["slug"] == "feature-x"

    check = await check_flag(
        service, "feature-x", {"sub": "user-123", "segments": ["beta"]}
    )
    assert check == {"slug": "feature-x", "on": True}

    await delete_flag(service, "feature-x")
    assert await store.get("feature-x") is None
