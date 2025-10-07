from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError

from domains.platform.moderation.application.appeals.repository import (
    AppealsRepository,
    _build_engine,
)


@pytest.mark.asyncio
async def test_appeals_repository_records_and_fetches():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = AppealsRepository(engine)

    now = datetime.now(UTC)
    meta = {"history": [{"result": "approved"}]}
    saved = await repo.record_decision(
        "apl-1",
        status="approved",
        decided_at=now,
        decided_by="moderator",
        decision_reason="manual review",
        meta=meta,
    )
    assert saved["status"] == "approved"

    fetched = await repo.fetch_appeal("apl-1")
    assert fetched["decided_by"] == "moderator"
    assert fetched["meta"]["history"]


@pytest.mark.asyncio
async def test_appeals_repository_fetch_many_handles_missing():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = AppealsRepository(engine)

    await repo.record_decision(
        "apl-1",
        status="approved",
        decided_at=datetime.now(UTC),
        decided_by="moderator",
        decision_reason=None,
        meta={},
    )

    data = await repo.fetch_many(["apl-1", "apl-2", "apl-1"])
    assert set(data.keys()) == {"apl-1"}

    # empty / falsy ids should short-circuit
    assert await repo.fetch_many([None, ""]) == {}

    # corrupt meta should fallback to {}
    async with engine.begin() as conn:
        await conn.execute(
            sa_text("UPDATE moderation_appeals SET meta = :meta WHERE id = :id"),
            {"meta": "{", "id": "apl-1"},
        )
    updated = await repo.fetch_appeal("apl-1")
    assert updated["meta"] == {}


@pytest.mark.asyncio
async def test_appeals_repository_engine_none_paths():
    repo = AppealsRepository(None)
    assert await repo.fetch_many(["x"]) == {}
    assert await repo.fetch_appeal("x") is None
    assert (
        await repo.record_decision(
            "apl-x",
            status="rejected",
            decided_at=datetime.now(UTC),
            decided_by=None,
            decision_reason="",
            meta={},
        )
        is None
    )


class _BrokenEngine:
    def begin(self):
        class _Ctx:
            async def __aenter__(self_inner):
                raise SQLAlchemyError("boom")

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        return _Ctx()

    def connect(self):
        class _Conn:
            async def __aenter__(self_inner):
                raise SQLAlchemyError("boom")

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        return _Conn()


@pytest.mark.asyncio
async def test_appeals_repository_handles_persistence_errors():
    repo = AppealsRepository(_BrokenEngine())
    assert (
        await repo.record_decision(
            "apl-err",
            status="approved",
            decided_at=datetime.now(UTC),
            decided_by="moderator",
            decision_reason=None,
            meta={},
        )
        is None
    )


@pytest.mark.asyncio
async def test_appeals_repository_build_engine_helper():
    settings = SimpleNamespace(database_url="sqlite+aiosqlite:///:memory:")
    engine = _build_engine(settings)
    assert engine is None
