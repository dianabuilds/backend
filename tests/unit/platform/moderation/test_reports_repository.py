from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import create_async_engine

from domains.platform.moderation.application.reports.repository import (
    ReportsRepository,
)


@pytest.mark.asyncio
async def test_reports_repository_records_and_fetches():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = ReportsRepository(engine)

    resolved_at = datetime.now(UTC)
    await repo.record_resolution(
        "r-1",
        status="resolved",
        decision="dismiss",
        notes="handled",
        actor_id="user:42",
        resolved_at=resolved_at,
        payload={"source": "unit"},
    )

    fetched = await repo.fetch_many(["r-1"])
    assert "r-1" in fetched
    assert fetched["r-1"]["status"] == "resolved"
    assert fetched["r-1"]["decision"] == "dismiss"

    listing = await repo.list_reports(status="resolved", limit=10, cursor=None)
    assert listing["items"], "expected persisted report in listing"
    assert listing["items"][0]["status"] == "resolved"


@pytest.mark.asyncio
async def test_reports_repository_handles_multiple_ids():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = ReportsRepository(engine)

    await repo.record_resolution(
        "r-1",
        status="resolved",
        decision=None,
        notes=None,
        actor_id=None,
        resolved_at=datetime.now(UTC),
        payload={},
    )
    await repo.record_resolution(
        "r-2",
        status="valid",
        decision="ban",
        notes="serious",
        actor_id="moderator",
        resolved_at=datetime.now(UTC),
        payload={},
    )

    fetched = await repo.fetch_many(["r-2", "r-3", "r-1", "r-2"])
    assert set(fetched) == {"r-1", "r-2"}
    assert fetched["r-2"]["decision"] == "ban"


@pytest.mark.asyncio
async def test_reports_repository_filters_history_and_pagination():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = ReportsRepository(engine)
    now = datetime.now(UTC)

    await repo.record_resolution(
        "r-keep",
        status="resolved",
        decision="keep",
        notes="",
        actor_id="user:1",
        resolved_at=now,
        payload={},
    )
    await repo.record_resolution(
        "r-ban",
        status="valid",
        decision="ban",
        notes="harmful",
        actor_id="user:2",
        resolved_at=now - timedelta(days=1),
        payload={},
    )

    async with engine.begin() as conn:
        await conn.execute(
            sa_text(
                "UPDATE moderation_reports SET category=:cat, object_type=:obj, created_at=:created WHERE id=:id"
            ),
            {
                "cat": "abuse",
                "obj": "node",
                "created": (now - timedelta(hours=1)).isoformat(),
                "id": "r-keep",
            },
        )
        await conn.execute(
            sa_text(
                "UPDATE moderation_reports SET category=:cat, object_type=:obj, created_at=:created WHERE id=:id"
            ),
            {
                "cat": "spam",
                "obj": "comment",
                "created": (now - timedelta(days=2)).isoformat(),
                "id": "r-ban",
            },
        )

    # invalid cursor should be handled gracefully
    await repo.list_reports(limit=1, cursor="bad")

    result = await repo.list_reports(
        category="abuse",
        status="resolved",
        object_type="node",
        date_from=(now - timedelta(days=1)).isoformat(),
        date_to=(now + timedelta(days=1)).isoformat(),
        limit=1,
        cursor=None,
    )
    assert result["items"] and result["items"][0]["status"] == "resolved"
    assert result["next_cursor"] == "1"

    second_page = await repo.list_reports(
        category="abuse",
        status="resolved",
        object_type="node",
        limit=1,
        cursor=result["next_cursor"],
    )
    assert second_page["items"] == []

    # ensure history appends on subsequent resolution
    await repo.record_resolution(
        "r-keep",
        status="resolved",
        decision="dismiss",
        notes="final",
        actor_id="user:3",
        resolved_at=now + timedelta(minutes=5),
        payload={"stage": "final"},
    )
    details = await repo.fetch_many(["r-keep"])
    assert len(details["r-keep"]["updates"]) >= 2

    async with engine.begin() as conn:
        await conn.execute(
            sa_text("UPDATE moderation_reports SET meta = :meta WHERE id = :id"),
            {"meta": "{", "id": "r-keep"},
        )
    # invalid JSON should fall back to empty dict
    refreshed = await repo.fetch_many(["r-keep"])
    assert refreshed["r-keep"]["meta"] == {}


@pytest.mark.asyncio
async def test_reports_repository_fallback_without_engine():
    repo = ReportsRepository(None)
    result = await repo.list_reports(limit=5, cursor=None)
    assert result == {"items": [], "next_cursor": None}
    assert await repo.fetch_many(["any"]) == {}
    assert (
        await repo.record_resolution(
            "r-x",
            status="resolved",
            decision=None,
            notes=None,
            actor_id=None,
            resolved_at=datetime.now(UTC),
            payload={},
        )
        is None
    )
