from __future__ import annotations

import pytest

from domains.product.navigation.application.use_cases import relations_admin as admin
from domains.product.navigation.application.use_cases.relations_admin import (
    RelationsAdminService,
    RelationsUnavailableError,
    RelationsValidationError,
)


class StubGateway:
    def __init__(self, engine_available: bool = True):
        self.engine_available = engine_available
        self.calls: list[str] = []

    async def get_engine(self):
        self.calls.append("get_engine")
        if not self.engine_available:
            return None
        return object()


@pytest.mark.asyncio
async def test_list_strategies_merges_usage(monkeypatch):
    gateway = StubGateway()
    service = RelationsAdminService(gateway)

    async def fake_fetch_strategy_rows(engine):
        return [
            {
                "strategy": "tags",
                "weight": 1.0,
                "enabled": True,
                "updated_at": "2025-10-07T00:00:00Z",
                "meta": {},
            },
            {
                "strategy": "random",
                "weight": 0.5,
                "enabled": False,
                "updated_at": "2025-10-06T00:00:00Z",
                "meta": {},
            },
        ]

    async def fake_fetch_usage_rows(engine):
        return {
            "tags": {"links": 10, "score": 5.0},
            "random": {"links": 5, "score": 1.0},
        }

    monkeypatch.setattr(admin, "fetch_strategy_rows", fake_fetch_strategy_rows)
    monkeypatch.setattr(admin, "fetch_usage_rows", fake_fetch_usage_rows)

    result = await service.list_strategies()

    assert result[0]["links"] == 10
    assert result[0]["usage_share"] == pytest.approx(10 / 15)
    assert result[1]["links"] == 5
    assert result[1]["usage_share"] == pytest.approx(5 / 15)


@pytest.mark.asyncio
async def test_update_strategy_validates_weight(monkeypatch):
    gateway = StubGateway()
    service = RelationsAdminService(gateway)

    with pytest.raises(RelationsValidationError):
        await service.update_strategy("tags", {"weight": "not-number"})

    with pytest.raises(RelationsValidationError):
        await service.update_strategy("tags", {"weight": -1})


@pytest.mark.asyncio
async def test_update_strategy_produces_payload(monkeypatch):
    gateway = StubGateway()
    service = RelationsAdminService(gateway)

    async def fake_update_strategy_row(engine, strategy, *, weight, enabled, meta_json):
        assert strategy == "tags"
        assert weight == 2.0
        assert enabled is True
        assert meta_json == "{}"
        return {
            "weight": 2.0,
            "enabled": True,
            "updated_at": "2025-10-07T00:00:00Z",
            "meta": {},
        }

    async def fake_usage_rows(engine):
        return {"tags": {"links": 4}}

    monkeypatch.setattr(admin, "update_strategy_row", fake_update_strategy_row)
    monkeypatch.setattr(admin, "fetch_usage_rows", fake_usage_rows)
    monkeypatch.setattr(admin, "fetch_strategy_rows", lambda engine: [])

    result = await service.update_strategy(
        "tags",
        {"weight": 2, "enabled": True, "meta": {}},
    )

    assert result["strategy"] == "tags"
    assert result["links"] == 4


@pytest.mark.asyncio
async def test_update_strategy_unavailable(monkeypatch):
    gateway = StubGateway(engine_available=False)
    service = RelationsAdminService(gateway)

    with pytest.raises(RelationsUnavailableError):
        await service.update_strategy("tags", {})


@pytest.mark.asyncio
async def test_update_strategy_rejects_invalid_meta(monkeypatch):
    gateway = StubGateway()
    service = RelationsAdminService(gateway)

    with pytest.raises(RelationsValidationError):
        await service.update_strategy("tags", {"meta": object()})


@pytest.mark.asyncio
async def test_overview_builds_metrics(monkeypatch):
    gateway = StubGateway()
    service = RelationsAdminService(gateway)

    async def fake_fetch_strategy_rows(engine):
        return [
            {
                "strategy": "tags",
                "weight": 1.0,
                "enabled": True,
                "updated_at": "2025-10-07T00:00:00Z",
            },
            {
                "strategy": "embedding",
                "weight": 0.5,
                "enabled": True,
                "updated_at": "2025-10-06T00:00:00Z",
            },
        ]

    async def fake_fetch_usage_rows(engine):
        return {"tags": {"links": 6}, "embedding": {"links": 4}}

    popular_calls: list[str] = []

    async def fake_fetch_top_relations(engine, key, *, limit):
        popular_calls.append((key, limit))
        return [{"source_id": 1, "target_id": 2, "algo": key}]

    monkeypatch.setattr(admin, "fetch_strategy_rows", fake_fetch_strategy_rows)
    monkeypatch.setattr(admin, "fetch_usage_rows", fake_fetch_usage_rows)
    monkeypatch.setattr(admin, "fetch_top_relations", fake_fetch_top_relations)

    payload = await service.overview()

    assert payload["diversity"]["coverage"] == 1.0
    assert payload["diversity"]["gini"] == pytest.approx(0.48)
    assert payload["diversity"]["entropy"] == pytest.approx(0.97095, rel=1e-3)
    assert {call[0] for call in popular_calls} == {"tags", "embedding"}
    assert payload["popular"]["tags"]


@pytest.mark.asyncio
async def test_top_relations_returns_payload(monkeypatch):
    gateway = StubGateway()
    service = RelationsAdminService(gateway)

    async def fake_fetch_top_relations(engine, key, *, limit):
        return [{"source_id": 1, "target_id": 2, "algo": key}]

    monkeypatch.setattr(admin, "fetch_top_relations", fake_fetch_top_relations)

    payload = await service.top_relations("fts", limit=3)

    assert payload["strategy"] == "embedding"
    assert payload["items"][0]["algo"] == "embedding"


@pytest.mark.asyncio
async def test_build_relations_admin_service_uses_container(monkeypatch):
    container = object()
    observed = {}

    async def fake_ensure_engine(arg):
        observed["container"] = arg
        return "engine"

    monkeypatch.setattr(admin, "ensure_engine", fake_ensure_engine)

    service = admin.build_relations_admin_service(container)
    engine = await service.gateway.get_engine()

    assert engine == "engine"
    assert observed["container"] is container
