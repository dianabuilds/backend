import pytest
from uuid import uuid4

from app.domains.content import service as content_service
from app.domains.system import events
from app.domains.navigation.application.cache_singleton import navcache


@pytest.mark.asyncio
async def test_content_published_triggers_index_and_cache(monkeypatch):
    called = {"index": 0, "cache": 0}

    async def fake_index(content_id):
        called["index"] += 1

    async def fake_cache_all():
        called["cache"] += 1

    monkeypatch.setattr(events.handlers, "index_content", fake_index)
    monkeypatch.setattr(navcache, "invalidate_compass_all", fake_cache_all)

    await content_service.publish_content(uuid4(), "slug", uuid4())

    assert called["index"] == 1
    assert called["cache"] == 1
