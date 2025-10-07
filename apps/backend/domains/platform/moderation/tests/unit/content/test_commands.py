from __future__ import annotations

from datetime import UTC, datetime

import pytest

from domains.platform.moderation.application.content import commands
from domains.platform.moderation.application.content.repository import (
    ContentRepository,
)


class StubRepository(ContentRepository):
    def __init__(self, record: dict | None = None):
        super().__init__(None)
        self._record = record

    async def record_decision(self, content_id: str, *, action, reason, actor_id, payload):  # type: ignore[override]
        return self._record


@pytest.mark.asyncio
async def test_decide_content_without_repository(moderation_service, moderation_data):
    service = moderation_service
    content_id = moderation_data["content"]["pending"]
    service._now = lambda: datetime(2025, 10, 4, 12, tzinfo=UTC)  # type: ignore[attr-defined]

    result = await commands.decide_content(
        service,
        content_id,
        {"action": "hide", "reason": "spam"},
        actor_id="moderator:lynx",
    )

    assert result["status"] == "hidden"
    assert result["decision"]["actor"] == "moderator:lynx"
    assert "db_state" not in result


@pytest.mark.asyncio
async def test_decide_content_merges_db_record(moderation_service, moderation_data):
    service = moderation_service
    content_id = moderation_data["content"]["pending"]
    service._now = lambda: datetime(2025, 10, 4, 12, tzinfo=UTC)  # type: ignore[attr-defined]

    repo = StubRepository(
        {
            "status": "resolved",
            "history_entry": {
                "decided_at": "2025-10-04T12:00:00Z",
                "status": "resolved",
            },
        }
    )

    result = await commands.decide_content(
        service,
        content_id,
        {"action": "keep"},
        actor_id="moderator:lynx",
        repository=repo,
    )

    assert result["moderation_status"] == "resolved"
    assert result["decision"]["status"] == "resolved"
    assert result["db_state"]["status"] == "resolved"
