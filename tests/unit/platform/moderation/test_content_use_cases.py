from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from domains.platform.moderation.application.content import commands as content_commands
from domains.platform.moderation.application.content import queries as content_queries
from domains.platform.moderation.domain.dtos import (
    ContentStatus,
    ContentSummary,
    ContentType,
)
from domains.platform.moderation.domain.records import ContentRecord


class StubRepo:
    def __init__(self) -> None:
        self.decisions: list[dict[str, Any]] = []

    async def list_queue(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "items": [
                ContentSummary(
                    id="c1",
                    type=ContentType.node,
                    author_id="u1",
                    created_at=datetime(2025, 1, 1, tzinfo=UTC).isoformat(),
                    preview="",
                    ai_labels=[],
                    complaints_count=0,
                    status=ContentStatus.pending,
                    moderation_history=[],
                    reports=[],
                    meta={},
                )
            ],
            "next_cursor": None,
        }

    async def load_content_details(self, content_id: str) -> dict[str, Any]:
        if content_id != "c1":
            raise KeyError(content_id)
        return {
            "status": "resolved",
            "decided_at": datetime(2025, 1, 2, tzinfo=UTC),
            "decided_by": "moderator",
            "meta": {"source": "repo", "moderation_status": "resolved"},
        }

    async def record_decision(
        self,
        content_id: str,
        *,
        action: str,
        reason: str | None,
        actor_id: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        entry = {
            "content_id": content_id,
            "action": action,
            "reason": reason,
            "actor_id": actor_id,
            "payload": payload,
        }
        self.decisions.append(entry)
        return {
            "status": "resolved",
            "decided_at": datetime(2025, 1, 2, tzinfo=UTC),
            "decided_by": actor_id or "system",
            "meta": {"source": "repo"},
        }


class StubService:
    def __init__(self) -> None:
        self._content = {
            "c1": ContentRecord(
                id="c1",
                content_type=ContentType.node,
                author_id="u1",
                created_at=datetime(2025, 1, 1, tzinfo=UTC),
                preview="",
                ai_labels=(),
                report_ids=(),
                status=ContentStatus.pending,
                moderation_history=[],
                meta={},
            )
        }
        self._reports: dict[str, dict[str, Any]] = {}
        from asyncio import Lock

        self._lock = Lock()

    async def decide_content(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "status": "resolved",
            "decided_at": datetime(2025, 1, 2, tzinfo=UTC),
            "decided_by": kwargs.get("actor_id"),
            "meta": {"source": "service"},
        }

    async def edit_content(
        self, content_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if content_id not in self._content:
            raise KeyError(content_id)
        record = self._content[content_id]
        record.meta.update(payload)
        return {"content_id": content_id, "meta": dict(record.meta)}

    def _now(self) -> datetime:
        return datetime(2025, 1, 2, tzinfo=UTC)


def _run(awaitable):
    return asyncio.run(awaitable)  # type: ignore[arg-type]


def test_list_queue_returns_payload() -> None:
    repo = StubRepo()
    result = _run(
        content_queries.list_queue(
            repo,
            content_type=ContentType.node,
            limit=10,
        )
    )
    assert result["items"] and result["items"][0]["id"] == "c1"


def test_get_content_merges_db_info() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(content_queries.get_content(service, "c1", repository=repo))
    assert result.meta.get("source") == "repo"
    assert result.meta.get("moderation_status") == "resolved"


def test_get_content_not_found() -> None:
    service = StubService()
    with pytest.raises(KeyError):
        _run(content_queries.get_content(service, "missing", repository=None))


def test_decide_content_returns_payload() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(
        content_commands.decide_content(
            service,
            "c1",
            {"action": "allow"},
            actor_id="mod",
            repository=repo,
        )
    )
    assert result["status"] == "resolved"
    assert repo.decisions and repo.decisions[0]["content_id"] == "c1"


def test_edit_content_propagates_error() -> None:
    service = StubService()
    with pytest.raises(KeyError):
        _run(content_commands.edit_content(service, "missing", {}))
