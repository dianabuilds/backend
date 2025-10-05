from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from domains.platform.moderation.application.content.exceptions import (
    ModerationContentError,
)
from domains.platform.moderation.application.content.repository import ContentRepository
from domains.platform.moderation.application.content.use_cases import (
    UseCaseResult,
    decide_content,
    edit_content,
    get_content,
    list_queue,
)
from domains.platform.moderation.domain.dtos import ContentSummary, ContentType
from domains.platform.moderation.domain.records import ContentRecord


class StubRepo(ContentRepository):
    def __init__(self) -> None:  # type: ignore[no-untyped-def]
        pass

    async def list_queue(self, **kwargs: Any) -> dict[str, Any]:
        return {"items": [{"id": "c1"}], "next_cursor": None}

    async def load_content_details(self, content_id: str) -> dict[str, Any]:
        return {
            "status": "resolved",
            "history_entry": {
                "status": "resolved",
                "decided_at": datetime(2025, 1, 1, tzinfo=UTC),
            },
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
                status=ContentSummary.model_fields["status"].default,
                moderation_history=(),
                meta={},
            )
        }
        self._reports: dict[str, dict[str, Any]] = {}
        from asyncio import Lock

        self._lock = Lock()

    async def decide_content(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"decision": {"status": "approved"}, "db_record": {"status": "resolved"}}

    async def edit_content(
        self, content_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if content_id not in self._content:
            raise KeyError(content_id)
        return {"id": content_id, **payload}


def _run(awaitable):
    return asyncio.get_event_loop().run_until_complete(awaitable)


def test_list_queue_returns_payload() -> None:
    repo = StubRepo()
    result = _run(list_queue(repo, content_type=None, limit=10))
    assert isinstance(result, UseCaseResult)
    assert result.payload["items"][0]["id"] == "c1"


def test_get_content_merges_db_info() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(get_content(service, "c1", repository=repo))
    assert result.payload["moderation_status"] == "resolved"


def test_get_content_not_found() -> None:
    service = StubService()
    try:
        _run(get_content(service, "missing", repository=None))
    except ModerationContentError as exc:
        assert exc.code == "content_not_found"
    else:
        raise AssertionError("expected ModerationContentError")


def test_decide_content_returns_payload() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(
        decide_content(
            service,
            repo,
            content_id="c1",
            payload={"status": "approved"},
            actor_id="mod",
        )
    )
    assert result.payload["moderation_status"] == "resolved"


def test_edit_content_propagates_error() -> None:
    service = StubService()
    try:
        _run(edit_content(service, content_id="missing", payload={}))
    except ModerationContentError:
        pass
    else:
        raise AssertionError("expected ModerationContentError")
