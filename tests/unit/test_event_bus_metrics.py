from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.system.events import (  # noqa: E402
    AchievementUnlocked,
    NodePublished,
    get_event_bus,
)
from app.domains.telemetry.application.event_metrics_facade import (
    event_metrics,  # noqa: E402
)


@pytest.mark.asyncio
async def test_event_bus_counts_events() -> None:
    event_metrics._counters.clear()
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
        )
    )
    snapshot = event_metrics.snapshot()
    assert snapshot[str(ws_id)]["node.publish"] == 1
    assert snapshot[str(ws_id)]["achievement"] == 1
