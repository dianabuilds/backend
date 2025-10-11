from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

from domains.product.navigation.infrastructure import relations as infra


class FakeResult:
    def __init__(
        self,
        rows: list[dict[str, Any]] | None = None,
        first: dict[str, Any] | None = None,
    ):
        self._rows = rows or []
        self._first = first

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        if self._first is not None:
            return self._first
        return self._rows[0] if self._rows else None


class FakeConnection:
    def __init__(self, *responses: Any, in_tx: bool = False):
        self._responses = list(responses)
        self._in_tx = in_tx
        self.rollback_called = False

    async def execute(self, statement, params=None):  # noqa: D401 - simple stub
        if not self._responses:
            return FakeResult()
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if callable(response):
            response = response(statement, params)
        if isinstance(response, FakeResult):
            return response
        if isinstance(response, list):
            return FakeResult(rows=response)
        if isinstance(response, dict):
            return FakeResult(first=response)
        return FakeResult()

    def in_transaction(self) -> bool:
        return self._in_tx

    async def rollback(self) -> None:
        self.rollback_called = True


class FakeContext:
    def __init__(self, connection: FakeConnection):
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeEngine:
    def __init__(self, *connections: FakeConnection):
        self._connections = list(connections)

    def begin(self):
        if not self._connections:
            raise AssertionError("no connections left")
        return FakeContext(self._connections.pop(0))


@pytest.mark.asyncio
async def test_fetch_strategy_rows_parses_and_deduplicates():
    rows = [
        {
            "strategy": "tags",
            "weight": "2",
            "enabled": True,
            "updated_at": datetime(2025, 10, 10, 12, 0, 0),
            "meta": '{"limit": 3}',
        },
        {
            "strategy": "tags",
            "weight": 1,
            "enabled": False,
            "updated_at": None,
            "meta": "not-json",
        },
        {
            "strategy": "semantic",
            "weight": "0.5",
            "enabled": True,
            "updated_at": "2025-10-11T00:00:00Z",
            "meta": None,
        },
    ]
    engine = FakeEngine(FakeConnection(rows))

    result = await infra.fetch_strategy_rows(engine)

    assert len(result) == 2
    assert result[0] == {
        "strategy": "tags",
        "weight": 2.0,
        "enabled": True,
        "updated_at": "2025-10-10T12:00:00Z",
        "meta": {"limit": 3},
    }
    assert result[1]["strategy"] == "embedding"
    assert result[1]["meta"] == {}


@pytest.mark.asyncio
async def test_fetch_strategy_rows_handles_errors():
    engine = FakeEngine(FakeConnection(SQLAlchemyError("boom")))

    result = await infra.fetch_strategy_rows(engine)

    assert result == []


@pytest.mark.asyncio
async def test_fetch_usage_rows_aggregates_metrics():
    rows = [
        {"algo": "fts", "links": 2, "total_score": 1.5},
        {"algo": "embedding", "links": "3", "total_score": 2.0},
        {"algo": "random", "links": None, "total_score": None},
    ]
    engine = FakeEngine(FakeConnection(rows))

    result = await infra.fetch_usage_rows(engine)

    assert result["embedding"]["links"] == 5
    assert result["embedding"]["score"] == pytest.approx(3.5)
    assert result["embedding"]["raw"] == {"fts": 2, "embedding": 3}
    assert result["random"]["links"] == 0


@pytest.mark.asyncio
async def test_fetch_usage_rows_handles_errors():
    engine = FakeEngine(FakeConnection(SQLAlchemyError("fail")))

    result = await infra.fetch_usage_rows(engine)

    assert result == {}


@pytest.mark.asyncio
async def test_fetch_top_relations_formats_rows(monkeypatch):
    rows = [
        {
            "source_id": "1",
            "target_id": "2",
            "algo": "FTS",
            "score": "1.7",
            "updated_at": datetime(2025, 10, 10, 13, 0, 0),
            "source_title": "Source",
            "source_slug": "source",
            "target_title": "Target",
            "target_slug": "target",
        },
        {
            "source_id": None,
            "target_id": "3",
            "algo": "vector",
            "score": 0,
            "updated_at": None,
            "source_title": "Missing",
            "source_slug": "missing",
            "target_title": "Other",
            "target_slug": "other",
        },
    ]
    engine = FakeEngine(FakeConnection(rows))

    result = await infra.fetch_top_relations(engine, "embedding", limit=5)

    assert len(result) == 1
    item = result[0]
    assert item["source_id"] == 1
    assert item["target_id"] == 2
    assert item["algo"] == "embedding"
    assert item["score"] == pytest.approx(1.7)
    assert item["updated_at"] == "2025-10-10T13:00:00Z"


@pytest.mark.asyncio
async def test_fetch_top_relations_handles_errors():
    engine = FakeEngine(FakeConnection(SQLAlchemyError("bad")))

    result = await infra.fetch_top_relations(engine, "tags", limit=3)

    assert result == []


@pytest.mark.asyncio
async def test_fetch_top_relations_without_sources(monkeypatch):
    monkeypatch.setattr(infra, "algo_sources", lambda key: [])

    engine = FakeEngine()

    result = await infra.fetch_top_relations(engine, "unknown")

    assert result == []


@pytest.mark.asyncio
async def test_update_strategy_row_returns_payload():
    row = {
        "strategy": "tags",
        "weight": 1.0,
        "enabled": True,
        "updated_at": datetime(2025, 10, 11, 12, 0, 0),
        "meta": {"limit": 3},
    }
    engine = FakeEngine(FakeConnection(FakeResult(first=row)))

    result = await infra.update_strategy_row(
        engine,
        "tags",
        weight=1.0,
        enabled=True,
        meta_json="{}",
    )

    assert result == row


@pytest.mark.asyncio
async def test_update_strategy_row_handles_errors():
    engine = FakeEngine(FakeConnection(SQLAlchemyError("oops")))

    result = await infra.update_strategy_row(
        engine,
        "tags",
        weight=None,
        enabled=None,
        meta_json=None,
    )

    assert result is None
