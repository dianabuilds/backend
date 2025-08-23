from uuid import uuid4

import pytest

from app.domains.navigation.application.cache_singleton import navcache
from app.domains.nodes import service as node_service
from app.domains.system import events


@pytest.mark.asyncio
async def test_content_published_triggers_index_and_cache(monkeypatch):
    called = {"index": 0, "cache": 0}

    async def fake_index(content_id):
        called["index"] += 1

    async def fake_cache_all():
        called["cache"] += 1

    monkeypatch.setattr(events.handlers, "index_content", fake_index)
    monkeypatch.setattr(navcache, "invalidate_compass_all", fake_cache_all)

    await node_service.publish_content(uuid4(), "slug", uuid4())

    assert called["index"] == 1
    assert called["cache"] == 1
