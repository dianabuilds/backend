from __future__ import annotations

import logging
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.system.events.handlers import _Handlers, navcache  # noqa: E402
from app.domains.system.events.models import (  # noqa: E402
    NodeCreated,
    NodePublished,
    NodeUpdated,
)


@asynccontextmanager
async def _dummy_session() -> None:  # type: ignore[misc]
    yield None


async def _noop(*args, **kwargs) -> None:  # noqa: ANN401
    return None


async def _failing(*args, **kwargs) -> None:  # noqa: ANN401
    raise RuntimeError("fail")


def _make_handlers() -> _Handlers:
    h = _Handlers.__new__(_Handlers)
    h.db_session = _dummy_session
    h.update_node_embedding = _noop
    h.index_content = _noop
    return h


@pytest.mark.asyncio
async def test_handle_node_created_logs(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    h = _make_handlers()
    monkeypatch.setattr(navcache, "invalidate_compass_all", _failing)
    event = NodeCreated(node_id=1, slug="s", author_id=uuid.uuid4())
    with caplog.at_level(logging.ERROR):
        await h.handle_node_created(event)
    records = [r for r in caplog.records if getattr(r, "event", None) == event]
    assert len(records) == 1
    assert records[0].message == "navcache.invalidate_compass_all_failed"


@pytest.mark.asyncio
async def test_handle_node_updated_logs(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    h = _make_handlers()
    monkeypatch.setattr(navcache, "invalidate_navigation_by_node", _failing)
    monkeypatch.setattr(navcache, "invalidate_compass_all", _failing)
    event = NodeUpdated(node_id=1, slug="s", author_id=uuid.uuid4(), tags_changed=True)
    with caplog.at_level(logging.ERROR):
        await h.handle_node_updated(event)
    records = [r for r in caplog.records if getattr(r, "event", None) == event]
    messages = {r.message for r in records}
    assert messages == {
        "navcache.invalidate_navigation_by_node_failed",
        "navcache.invalidate_compass_all_failed",
    }


@pytest.mark.asyncio
async def test_handle_node_published_logs(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    h = _make_handlers()
    h.index_content = _failing
    monkeypatch.setattr(navcache, "invalidate_navigation_by_node", _failing)
    monkeypatch.setattr(navcache, "invalidate_modes_by_node", _noop)
    monkeypatch.setattr(navcache, "invalidate_compass_all", _noop)
    event = NodePublished(node_id=1, slug="s", author_id=uuid.uuid4())
    with caplog.at_level(logging.ERROR):
        await h.handle_node_published(event)
    records = [r for r in caplog.records if getattr(r, "event", None) == event]
    messages = {r.message for r in records}
    assert messages == {
        "index_content_failed",
        "navcache.invalidate_post_publish_failed",
    }
