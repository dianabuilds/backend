from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import create_async_engine

from domains.platform.moderation.application.tickets.repository import (
    TicketsRepository,
)


@pytest.mark.asyncio
async def test_tickets_repository_persists_ticket_and_messages():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = TicketsRepository(engine)

    now = datetime.now(UTC)
    await repo.record_ticket_update(
        "tic-1",
        status="new",
        priority="normal",
        assignee_id=None,
        updated_at=now,
        last_message_at=None,
        unread_count=0,
        meta={"channel": "email"},
    )

    ticket = await repo.fetch_ticket("tic-1")
    assert ticket["status"] == "new"
    assert ticket["meta"]["channel"] == "email"

    persisted = await repo.record_message(
        message_id="msg-1",
        ticket_id="tic-1",
        author_id="user-1",
        author_name="Support",
        text="Initial reply",
        internal=False,
        created_at=now,
        attachments=[],
    )
    assert persisted["ticket_id"] == "tic-1"

    messages = await repo.list_messages("tic-1", limit=10, cursor=None)
    assert messages["items"], "expected persisted message"
    assert messages["items"][0]["text"] == "Initial reply"


@pytest.mark.asyncio
async def test_tickets_repository_fetch_many_returns_map():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = TicketsRepository(engine)

    now = datetime.now(UTC)
    await repo.record_ticket_update(
        "tic-1",
        status="new",
        priority="normal",
        assignee_id=None,
        updated_at=now,
        last_message_at=None,
        unread_count=2,
        meta={},
    )
    await repo.record_ticket_update(
        "tic-2",
        status="progress",
        priority="high",
        assignee_id="agent-7",
        updated_at=now,
        last_message_at=now,
        unread_count=1,
        meta={"source": "unit"},
    )

    data = await repo.fetch_many(["tic-2", "tic-3", "tic-1", "tic-2"])
    assert set(data) == {"tic-1", "tic-2"}
    assert data["tic-2"]["priority"] == "high"


@pytest.mark.asyncio
async def test_tickets_repository_covers_pagination_and_decode():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    repo = TicketsRepository(engine)
    now = datetime.now(UTC)

    await repo.record_ticket_update(
        "tic-pag",
        status="waiting",
        priority="urgent",
        assignee_id="agent-9",
        updated_at=now,
        last_message_at=None,
        unread_count=5,
        meta={"channel": "chat"},
    )

    await repo.record_message(
        message_id="msg-a",
        ticket_id="tic-pag",
        author_id="user-1",
        author_name=None,
        text="hi",
        internal=False,
        created_at=now - timedelta(minutes=5),
        attachments=[{"name": "log.txt"}],
    )
    await repo.record_message(
        message_id="msg-b",
        ticket_id="tic-pag",
        author_id="user-2",
        author_name="Agent",
        text="reply",
        internal=True,
        created_at=now,
        attachments=[],
    )

    # override meta and attachments with invalid JSON to exercise fallback paths
    async with engine.begin() as conn:
        await conn.execute(
            sa_text("UPDATE moderation_tickets SET meta = :meta WHERE id = :id"),
            {"meta": "{", "id": "tic-pag"},
        )
        await conn.execute(
            sa_text(
                "UPDATE moderation_ticket_messages SET attachments = :att WHERE id = :id"
            ),
            {"att": "[", "id": "msg-b"},
        )

    # invalid cursor should be handled gracefully
    await repo.list_messages("tic-pag", limit=1, cursor="bad")

    page1 = await repo.list_messages("tic-pag", limit=1, cursor=None)
    assert page1["items"]
    assert page1["next_cursor"] == "1"

    page2 = await repo.list_messages("tic-pag", limit=1, cursor=page1["next_cursor"])
    assert page2["items"]

    ticket = await repo.fetch_ticket("tic-pag")
    assert ticket["meta"] == {}


@pytest.mark.asyncio
async def test_tickets_repository_handles_engine_none():
    repo = TicketsRepository(None)
    assert await repo.fetch_many(["any"]) == {}
    assert await repo.fetch_ticket("tic") is None
    result = await repo.list_messages("tic", limit=5, cursor=None)
    assert result == {"items": [], "next_cursor": None}
    # record functions should no-op without raising
    await repo.record_ticket_update(
        "tic",
        status="new",
        priority="low",
        assignee_id=None,
        updated_at=datetime.now(UTC),
        last_message_at=None,
        unread_count=0,
        meta={},
    )
    assert (
        await repo.record_message(
            message_id="msg",
            ticket_id="tic",
            author_id="user",
            author_name=None,
            text="ping",
            internal=False,
            created_at=datetime.now(UTC),
            attachments=[],
        )
        is None
    )
