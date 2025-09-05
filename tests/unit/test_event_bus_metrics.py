from __future__ import annotations

import importlib
import sys
import uuid

import pytest

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.system.events import (  # noqa: E402
    AchievementUnlocked,
    EventBus,
    NodePublished,
    get_event_bus,
)
from app.domains.telemetry.application.event_metrics_facade import (  # noqa: E402
    event_metrics,
)


@pytest.mark.asyncio
async def test_event_bus_counts_events() -> None:
    event_metrics.reset()
    bus = get_event_bus()
    ws_id = uuid.uuid4()
    await bus.publish(
        NodePublished(
            node_id=1,
            slug="s",
            author_id=uuid.uuid4(),
            workspace_id=ws_id,
        )
    )
    await bus.publish(
        AchievementUnlocked(
            achievement_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            workspace_id=ws_id,
            title="t",
            message="m",
        )
    )
    snapshot = event_metrics.snapshot()
    assert snapshot[str(ws_id)]["node.publish"] == 1
    assert snapshot[str(ws_id)]["achievement"] == 1


@pytest.mark.asyncio
async def test_handler_metrics_success() -> None:
    event_metrics.reset()
    bus = EventBus()

    async def handler(event: NodePublished) -> None:
        return None

    bus.subscribe(NodePublished, handler)
    await bus.publish(
        NodePublished(
            node_id=1,
            slug="s",
            author_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
        )
    )
    assert event_metrics._handler_counts["node.publish"]["handler"]["success"] == 1
    assert event_metrics._handler_time_count["node.publish"]["handler"] == 1


@pytest.mark.asyncio
async def test_handler_metrics_failure() -> None:
    event_metrics.reset()
    bus = EventBus()

    async def failing(event: NodePublished) -> None:
        raise RuntimeError("boom")

    bus.subscribe(NodePublished, failing)
    await bus.publish(
        NodePublished(
            node_id=1,
            slug="s",
            author_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
        )
    )
    assert event_metrics._handler_counts["node.publish"]["failing"]["failure"] == 1
    assert event_metrics._handler_time_count["node.publish"]["failing"] == 1
