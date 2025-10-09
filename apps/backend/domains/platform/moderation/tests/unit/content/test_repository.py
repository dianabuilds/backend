from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

from domains.platform.moderation.application.content.repository import (
    ContentRepository,
    coerce_status,
)
from domains.platform.moderation.domain.dtos import ContentStatus


class FakeResult:
    class _Mappings:
        def __init__(self, rows: list[dict[str, Any]]):
            self._rows = rows

        def all(self) -> list[dict[str, Any]]:
            return list(self._rows)

        def first(self) -> dict[str, Any] | None:
            return self._rows[0] if self._rows else None

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    def mappings(self) -> FakeResult._Mappings:
        return FakeResult._Mappings(self._rows)

    def scalar(self) -> Any | None:
        if not self._rows:
            return None
        first = self._rows[0]
        if isinstance(first, dict) and len(first) == 1:
            return next(iter(first.values()))
        return first


class FakeConnection:
    def __init__(
        self,
        handlers: list[
            tuple[
                Callable[[str], bool],
                Callable[[dict[str, Any] | None], list[dict[str, Any]]],
            ]
        ],
    ):
        self._handlers = handlers

    async def execute(self, statement, params: dict[str, Any] | None = None):
        sql = str(statement)
        for predicate, responder in self._handlers:
            if predicate(sql):
                try:
                    rows = responder(params)
                except SQLAlchemyError:
                    raise
                except Exception as exc:  # pragma: no cover - defensive
                    raise AssertionError(f"Unhandled SQL {sql}: {exc}") from exc
                return FakeResult(rows)
        return FakeResult()


class FakeBegin:
    def __init__(self, handlers):
        self._handlers = handlers

    async def __aenter__(self):
        return FakeConnection(self._handlers)

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeEngine:
    def __init__(self, handlers):
        self._handlers = handlers

    def begin(self):
        return FakeBegin(self._handlers)


@pytest.fixture(autouse=True)
def reset_schema_flags(monkeypatch):
    from domains.platform.moderation.application import content

    repo_mod = content.repository
    monkeypatch.setattr(repo_mod, "_SCHEMA_READY", False)
    monkeypatch.setattr(repo_mod, "_MODERATION_SCHEMA_STATEMENTS", [])
    monkeypatch.setattr(repo_mod, "_MODERATION_SCHEMA_DO_BLOCKS", [])
    yield
    monkeypatch.setattr(repo_mod, "_SCHEMA_READY", False)


@pytest.mark.asyncio
async def test_list_queue_returns_rows(monkeypatch):
    created_at = datetime(2025, 10, 4, 12, tzinfo=UTC)
    rows = [
        {
            "id": 41,
            "author_id": "user-123",
            "title": "Demo node",
            "node_status": "published",
            "created_at": created_at,
            "moderation_status": "resolved",
            "moderation_status_updated_at": created_at,
            "last_action": "hide",
            "last_status": "hidden",
            "last_reason": "spam",
            "last_actor_id": "moderator:lynx",
            "last_decided_at": created_at,
        }
    ]

    handlers = [
        (lambda sql: "SELECT n.id" in sql, lambda params: rows),
    ]

    repo = ContentRepository(FakeEngine(handlers))
    result = await repo.list_queue(
        content_type=None,
        status=None,
        moderation_status=None,
        ai_label=None,
        has_reports=None,
        author_id=None,
        date_from=None,
        date_to=None,
        limit=20,
        cursor=None,
    )

    assert result["next_cursor"] is None
    item = result["items"][0]
    assert item["id"] == "41"
    assert item["meta"]["moderation_status"] == "resolved"
    assert item["moderation_history"][0]["actor"] == "user:moderator:lynx"


@pytest.mark.asyncio
async def test_load_content_details_returns_history(monkeypatch):
    created_at = datetime(2025, 10, 4, 12, tzinfo=UTC)
    node_rows = [
        {
            "id": 41,
            "author_id": "user-123",
            "title": "Demo node",
            "node_status": "published",
            "created_at": created_at,
            "moderation_status": "pending",
            "moderation_status_updated_at": created_at,
        }
    ]
    history_rows = [
        {
            "action": "hide",
            "status": "hidden",
            "reason": "spam",
            "actor_id": "moderator:lynx",
            "decided_at": created_at,
            "payload": {"note": "auto"},
        }
    ]

    handlers = [
        (
            lambda sql: "FROM nodes WHERE id" in sql and "SELECT action" not in sql,
            lambda params: node_rows,
        ),
        (
            lambda sql: "FROM node_moderation_history" in sql,
            lambda params: history_rows,
        ),
    ]

    repo = ContentRepository(FakeEngine(handlers))
    details = await repo.load_content_details("41")
    assert details is not None
    assert details["id"] == "41"
    assert details["moderation_history"][0]["actor"] == "user:moderator:lynx"


@pytest.mark.asyncio
async def test_record_decision_updates_rows(monkeypatch):
    node_row = [
        {
            "moderation_status": "resolved",
            "moderation_status_updated_at": datetime(2025, 10, 4, 13, tzinfo=UTC),
        }
    ]
    history_row = [
        {
            "action": "hide",
            "status": "hidden",
            "reason": "spam",
            "actor_id": "moderator:lynx",
            "decided_at": datetime(2025, 10, 4, 13, tzinfo=UTC),
            "payload": {"note": "auto"},
        }
    ]

    handlers = [
        (
            lambda sql: "INSERT INTO node_moderation_history" in sql,
            lambda params: history_row,
        ),
        (
            lambda sql: "SELECT moderation_status, moderation_status_updated_at" in sql,
            lambda params: node_row,
        ),
    ]

    repo = ContentRepository(FakeEngine(handlers))
    record = await repo.record_decision(
        "41",
        action="hide",
        reason="spam",
        actor_id="moderator:lynx",
        payload={"foo": "bar"},
    )
    assert record is not None
    assert record["status"] == "resolved"
    assert record["history_entry"]["status"] == "hidden"


@pytest.mark.asyncio
async def test_repository_handles_missing_engine():
    repo = ContentRepository(None)
    queue = await repo.list_queue(
        content_type=None,
        status=None,
        moderation_status=None,
        ai_label=None,
        has_reports=None,
        author_id=None,
        date_from=None,
        date_to=None,
        limit=10,
        cursor=None,
    )
    assert queue == {"items": [], "next_cursor": None}
    assert await repo.load_content_details("1") is None
    assert (
        await repo.record_decision(
            "1", action="hide", reason=None, actor_id=None, payload={}
        )
        is None
    )


def test_coerce_status_handles_invalid():
    assert coerce_status("resolved") == ContentStatus.resolved
    assert coerce_status(None) == ContentStatus.pending
