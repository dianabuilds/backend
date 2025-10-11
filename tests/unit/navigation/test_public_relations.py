from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from domains.product.navigation.api.public import relations as relations_module


class FakeResult:
    def __init__(self, rows=None, first=None):
        self._rows = rows
        self._first = first

    def mappings(self):
        return self

    def all(self):
        return self._rows or []

    def first(self):
        if self._first is not None:
            return self._first
        rows = self._rows or []
        return rows[0] if rows else None


class SequencedConnection:
    def __init__(self, *responses: Any, in_tx: bool = False):
        self._responses = list(responses)
        self._in_tx = in_tx
        self.rollback_called = False

    async def execute(self, statement, params=None):
        if not self._responses:
            return FakeResult(rows=[])
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
        return FakeResult(rows=[])

    def in_transaction(self) -> bool:
        return self._in_tx

    async def rollback(self) -> None:
        self.rollback_called = True


class RecordingConnection:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def execute(self, statement, params=None):
        self.calls.append((str(statement), dict(params or {})))
        return FakeResult(rows=[])

    def in_transaction(self) -> bool:
        return False

    async def rollback(self) -> None:
        return None


class Context:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class StubEngine:
    def __init__(
        self,
        *,
        connect_connections: list[SequencedConnection],
        begin_connections: list[Any],
    ):
        self._connect_connections = connect_connections
        self._begin_connections = begin_connections

    def connect(self):
        if not self._connect_connections:
            raise AssertionError("no connect connections left")
        return Context(self._connect_connections.pop(0))

    def begin(self):
        if not self._begin_connections:
            raise AssertionError("no begin connections left")
        return Context(self._begin_connections.pop(0))


@pytest.fixture()
def app(monkeypatch):
    router = APIRouter()
    relations_module.register_relations_routes(router)
    application = FastAPI()
    application.include_router(router)

    async def override_get_container():
        return SimpleContainer()

    async def override_get_current_user():
        return {"sub": "42", "role": "user"}

    application.dependency_overrides[relations_module.get_container] = (
        override_get_container
    )
    application.dependency_overrides[relations_module.get_current_user] = (
        override_get_current_user
    )

    return application


@dataclass
class SimpleSettings:
    nav_related_ttl: int = 3600


@dataclass
class SimpleContainer:
    settings: SimpleSettings = field(default_factory=SimpleSettings)


def test_related_nodes_returns_empty_when_engine_missing(app, monkeypatch):
    async def fake_ensure_engine(container):
        return None

    monkeypatch.setattr(relations_module, "ensure_engine", fake_ensure_engine)

    client = TestClient(app)
    response = client.get("/related/1")

    assert response.status_code == 200
    assert response.json() == []


def test_related_nodes_returns_not_found(app, monkeypatch):
    first_conn = SequencedConnection(None)
    engine = StubEngine(connect_connections=[first_conn], begin_connections=[])

    async def fake_ensure_engine(container):
        return engine

    monkeypatch.setattr(relations_module, "ensure_engine", fake_ensure_engine)

    client = TestClient(app)
    response = client.get("/related/1")

    assert response.status_code == 404


def test_related_nodes_returns_empty_for_dev_blog(app, monkeypatch):
    node_info_conn = SequencedConnection(
        {"author_id": "1", "is_public": True, "is_dev_blog": True}
    )
    engine = StubEngine(connect_connections=[node_info_conn], begin_connections=[])

    async def fake_ensure_engine(container):
        return engine

    monkeypatch.setattr(relations_module, "ensure_engine", fake_ensure_engine)

    client = TestClient(app)
    response = client.get("/related/1")

    assert response.status_code == 200
    assert response.json() == []


def test_related_nodes_mix_merges_streams_and_caches(app, monkeypatch):
    node_info_conn = SequencedConnection(
        {"author_id": "42", "is_public": True, "is_dev_blog": False}
    )
    query_conn = SequencedConnection(
        {"title": "Alpha"},
        [
            {
                "id": 2,
                "slug": "beta",
                "title": "Beta",
                "cover_url": "beta.jpg",
                "is_public": True,
                "score": 3,
            }
        ],
        [
            {
                "id": 3,
                "slug": "gamma",
                "title": "Gamma",
                "cover_url": "gamma.jpg",
                "is_public": False,
                "score": 2,
            },
            {
                "id": 4,
                "slug": "delta",
                "title": "Delta",
                "cover_url": None,
                "is_public": True,
                "score": 1,
            },
        ],
    )
    store_fts = RecordingConnection()
    store_tags = RecordingConnection()
    engine = StubEngine(
        connect_connections=[node_info_conn, query_conn],
        begin_connections=[
            SequencedConnection([]),
            SequencedConnection([]),
            store_fts,
            store_tags,
        ],
    )

    async def fake_ensure_engine(container):
        return engine

    monkeypatch.setattr(relations_module, "ensure_engine", fake_ensure_engine)

    client = TestClient(app)
    response = client.get("/related/10", params={"algo": "mix", "limit": 3})

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data] == [3, 2, 4]
    assert data[0]["reason"] == "tags"
    assert data[1]["reason"] == "fts"
    assert len(store_fts.calls) == 1
    assert len(store_tags.calls) == 2
