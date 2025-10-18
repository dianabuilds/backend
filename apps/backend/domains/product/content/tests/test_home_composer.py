import asyncio
import logging
import uuid
from datetime import UTC, datetime

import pytest

from domains.product.content.application import (
    DevBlogDataService,
    HomeComposer,
    InMemoryHomeCache,
    NodeDataService,
    QuestDataService,
)
from domains.product.content.domain import HomeConfig, HomeConfigStatus


def _make_config(
    *, blocks: list[dict], slug: str = "main", version: int = 1
) -> HomeConfig:
    now = datetime.now(UTC)
    return HomeConfig(
        id=uuid.uuid4(),
        slug=slug,
        version=version,
        status=HomeConfigStatus.PUBLISHED,
        data={"blocks": blocks},
        created_by="system",
        updated_by="editor",
        created_at=now,
        updated_at=now,
        published_at=now,
        draft_of=None,
    )


async def _empty_many(_ids):
    return []


async def _empty_auto(_tag, _limit, _order):
    return []


@pytest.mark.asyncio()
async def test_compose_manual_preserves_order_and_logs_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(
        logging.INFO, logger="domains.product.content.application.home_composer"
    )

    cards = {
        "1": {"id": "1", "title": "First"},
        "2": {"id": "2", "title": "Second"},
    }

    async def fetch_many(ids):
        return [cards[str(i)] for i in ids if str(i) in cards]

    node_service = NodeDataService(fetch_many=fetch_many, fetch_filtered=_empty_auto)
    quest_service = QuestDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    dev_blog_service = DevBlogDataService(
        fetch_many=_empty_many, fetch_filtered=_empty_auto
    )

    composer = HomeComposer(
        cache=InMemoryHomeCache(),
        node_service=node_service,
        quest_service=quest_service,
        dev_blog_service=dev_blog_service,
    )

    config = _make_config(
        blocks=[
            {
                "id": "nodes",
                "type": "nodes_carousel",
                "enabled": True,
                "dataSource": {
                    "mode": "manual",
                    "entity": "node",
                    "items": ["1", "2", "999"],
                },
            }
        ]
    )

    result = await composer.compose(config, use_cache=False)

    assert result["blocks"]
    block = result["blocks"][0]
    assert [item["id"] for item in block["items"]] == ["1", "2"]
    assert result["fallbacks"] == []
    assert any(
        rec.message == "home.manual_source_missing_items" for rec in caplog.records
    )


@pytest.mark.asyncio()
async def test_compose_auto_enforces_limit_and_filter() -> None:
    recorded: dict[str, tuple[str | None, int, str | None]] = {}

    async def dev_blog_auto(tag, limit, order):
        recorded["params"] = (tag, limit, order)
        return [{"id": f"post-{idx}"} for idx in range(15)]

    node_service = NodeDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    quest_service = QuestDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    dev_blog_service = DevBlogDataService(
        fetch_many=_empty_many, fetch_filtered=dev_blog_auto
    )

    composer = HomeComposer(
        cache=InMemoryHomeCache(),
        node_service=node_service,
        quest_service=quest_service,
        dev_blog_service=dev_blog_service,
        max_auto_items=12,
        auto_timeout=1.0,
    )

    config = _make_config(
        blocks=[
            {
                "id": "blog",
                "type": "dev_blog_list",
                "enabled": True,
                "dataSource": {
                    "mode": "auto",
                    "entity": "dev_blog",
                    "filter": {"tag": "dev", "limit": 20, "order": "published_desc"},
                },
            }
        ]
    )

    result = await composer.compose(config, use_cache=False)

    assert recorded["params"] == ("dev", 12, "published_desc")
    assert result["blocks"]
    assert len(result["blocks"][0]["items"]) == 12


@pytest.mark.asyncio()
async def test_compose_error_creates_fallback() -> None:
    async def failing_fetch(ids):
        raise RuntimeError("boom")

    node_service = NodeDataService(fetch_many=failing_fetch, fetch_filtered=_empty_auto)
    quest_service = QuestDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    dev_blog_service = DevBlogDataService(
        fetch_many=_empty_many, fetch_filtered=_empty_auto
    )

    composer = HomeComposer(
        cache=InMemoryHomeCache(),
        node_service=node_service,
        quest_service=quest_service,
        dev_blog_service=dev_blog_service,
    )

    config = _make_config(
        blocks=[
            {
                "id": "nodes",
                "type": "nodes_carousel",
                "enabled": True,
                "dataSource": {
                    "mode": "manual",
                    "entity": "node",
                    "items": ["1"],
                },
            }
        ]
    )

    result = await composer.compose(config, use_cache=False)

    assert result["blocks"] == []
    assert result["fallbacks"]
    fallback = result["fallbacks"][0]
    assert fallback["id"] == "nodes"
    assert fallback["reason"] == "error"


@pytest.mark.asyncio()
async def test_compose_timeout_creates_timeout_fallback() -> None:
    async def slow_auto(tag, limit, order):
        await asyncio.sleep(0.05)
        return [{"id": "late"}]

    node_service = NodeDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    quest_service = QuestDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    dev_blog_service = DevBlogDataService(
        fetch_many=_empty_many, fetch_filtered=slow_auto
    )

    composer = HomeComposer(
        cache=InMemoryHomeCache(),
        node_service=node_service,
        quest_service=quest_service,
        dev_blog_service=dev_blog_service,
        auto_timeout=0.01,
    )

    config = _make_config(
        blocks=[
            {
                "id": "blog",
                "type": "dev_blog_list",
                "enabled": True,
                "dataSource": {
                    "mode": "auto",
                    "entity": "dev_blog",
                    "filter": {"tag": "dev", "limit": 5},
                },
            }
        ]
    )

    result = await composer.compose(config, use_cache=False)

    assert result["blocks"] == []
    assert result["fallbacks"]
    fallback = result["fallbacks"][0]
    assert fallback["reason"] == "timeout"


@pytest.mark.asyncio()
async def test_compose_reuses_cache_hit() -> None:
    fetch_calls = 0

    async def fetch_many(ids):
        nonlocal fetch_calls
        fetch_calls += 1
        return [{"id": str(i)} for i in ids]

    node_service = NodeDataService(fetch_many=fetch_many, fetch_filtered=_empty_auto)
    quest_service = QuestDataService(fetch_many=_empty_many, fetch_filtered=_empty_auto)
    dev_blog_service = DevBlogDataService(
        fetch_many=_empty_many, fetch_filtered=_empty_auto
    )

    composer = HomeComposer(
        cache=InMemoryHomeCache(),
        node_service=node_service,
        quest_service=quest_service,
        dev_blog_service=dev_blog_service,
    )

    blocks = [
        {
            "id": "nodes",
            "type": "nodes_carousel",
            "enabled": True,
            "dataSource": {"mode": "manual", "entity": "node", "items": ["1"]},
        }
    ]

    config_first = _make_config(blocks=blocks, version=1)
    result_first = await composer.compose(config_first)
    assert fetch_calls == 1

    config_second = _make_config(blocks=blocks, version=1)
    result_second = await composer.compose(config_second)
    assert fetch_calls == 1
    assert result_second == result_first
    assert result_second is not result_first


def test_home_metrics_smoke() -> None:
    prometheus_client = pytest.importorskip("prometheus_client")
    from domains.product.content.api import home_http  # noqa: F401, WPS433
    from domains.product.content.application import home_composer as hc  # noqa: WPS433

    if hc.HOME_CACHE_REQUESTS is None or hc.HOME_CACHE_HIT_RATIO is None:
        pytest.skip("prometheus client counters are not initialised")

    payload = prometheus_client.generate_latest()
    assert b"home_cache_requests_total" in payload
    assert b"home_cache_hit_ratio" in payload
    assert b"public_home_latency_seconds" in payload


@pytest.mark.asyncio()
async def test_compose_static_block_without_data_source() -> None:
    composer = HomeComposer(
        cache=InMemoryHomeCache(),
        node_service=NodeDataService(
            fetch_many=_empty_many, fetch_filtered=_empty_auto
        ),
        quest_service=QuestDataService(
            fetch_many=_empty_many, fetch_filtered=_empty_auto
        ),
        dev_blog_service=DevBlogDataService(
            fetch_many=_empty_many, fetch_filtered=_empty_auto
        ),
    )

    config = _make_config(
        blocks=[
            {
                "id": "hero-1",
                "type": "hero",
                "enabled": True,
                "title": "Hero",
                "slots": {
                    "headline": "Headline",
                    "cta": {"label": "Go", "href": "/"},
                },
            }
        ]
    )

    result = await composer.compose(config, use_cache=False)

    assert result["blocks"]
    block = result["blocks"][0]
    assert block["id"] == "hero-1"
    assert block["type"] == "hero"
    assert block.get("items") == []
    assert block.get("slots", {}).get("headline") == "Headline"
    assert result["fallbacks"] == []
