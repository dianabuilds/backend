from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.system.events import EventBus, NodePublished  # noqa: E402


@pytest.mark.asyncio
async def test_logs_after_three_failures(caplog: pytest.LogCaptureFixture) -> None:
    bus = EventBus()

    calls = 0

    async def handler(event: NodePublished) -> None:  # noqa: ARG001
        nonlocal calls
        calls += 1
        raise RuntimeError("fail")

    bus.subscribe(NodePublished, handler)
    event = NodePublished(node_id=1, slug="s", author_id=uuid.uuid4())

    with caplog.at_level(logging.ERROR):
        await bus.publish(event)

    assert calls == 3
    assert any("failed after" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_processed_limit_allows_reprocessing() -> None:
    bus = EventBus(processed_maxlen=2)
    seen: list[str] = []

    async def handler(event: NodePublished) -> None:
        seen.append(event.id)

    bus.subscribe(NodePublished, handler)
    events = [
        NodePublished(node_id=i, slug=f"s{i}", author_id=uuid.uuid4()) for i in range(3)
    ]
    for ev in events:
        await bus.publish(ev)

    assert events[0].id not in bus._processed_set
    await bus.publish(events[0])
    assert len(seen) == 4
    assert len(bus._processed_set) <= 2
    assert events[1].id not in bus._processed_set
