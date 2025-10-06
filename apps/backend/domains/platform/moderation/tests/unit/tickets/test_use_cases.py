from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ....application import tickets
from ....domain.dtos import TicketPriority, TicketStatus


@pytest.mark.asyncio
async def test_list_tickets_filters_by_status(moderation_service, moderation_data):
    service = moderation_service

    waiting = await tickets.list_tickets(service, status=TicketStatus.waiting)
    assert [item.id for item in waiting["items"]] == [
        moderation_data["tickets"]["waiting"]
    ]


@pytest.mark.asyncio
async def test_add_ticket_message_increments_unread(
    moderation_service, moderation_data
):
    service = moderation_service
    ticket_id = moderation_data["tickets"]["main"]

    dto = await tickets.add_ticket_message(
        service,
        ticket_id=ticket_id,
        body={"text": "still waiting", "attachments": []},
        author_id=moderation_data["users"]["bob"],
    )

    assert dto.ticket_id == ticket_id
    assert service._tickets[ticket_id].unread_count >= 2


@pytest.mark.asyncio
async def test_update_ticket_validates_status(moderation_service, moderation_data):
    service = moderation_service
    ticket_id = moderation_data["tickets"]["main"]

    with pytest.raises(ValueError):
        await tickets.update_ticket(service, ticket_id, {"status": "unknown"})


@pytest.mark.asyncio
async def test_list_ticket_messages_missing_ticket(moderation_service):
    service = moderation_service
    with pytest.raises(KeyError):
        await tickets.list_ticket_messages(service, ticket_id="missing")


class DummyTicketsRepository:
    def __init__(self) -> None:
        self.fetch_calls: list[list[str]] = []
        self.list_calls: list[tuple[str, int, str | None]] = []
        self.record_messages: list[dict] = []
        self.record_updates: list[dict] = []

    async def fetch_many(self, ticket_ids):
        ids = [str(tid) for tid in ticket_ids]
        self.fetch_calls.append(ids)
        updated_at = datetime(2025, 1, 4, tzinfo=UTC)
        return {
            tid: {
                "status": "progress",
                "priority": "urgent",
                "assignee_id": "agent-1",
                "updated_at": updated_at,
                "last_message_at": updated_at,
                "unread_count": 5,
                "meta": {"channel": "repo"},
            }
            for tid in ids
        }

    async def fetch_ticket(self, ticket_id):
        return {
            "status": "waiting",
            "priority": "low",
            "assignee_id": "agent-1",
            "updated_at": datetime(2025, 1, 4, tzinfo=UTC),
            "last_message_at": datetime(2025, 1, 4, 12, tzinfo=UTC),
            "unread_count": 2,
            "meta": {"channel": "repo"},
        }

    async def list_messages(self, ticket_id, *, limit, cursor):
        self.list_calls.append((ticket_id, limit, cursor))
        return {
            "items": [
                {
                    "id": "msg-db",
                    "ticket_id": ticket_id,
                    "author_id": "agent",
                    "author_name": "Agent",
                    "body": "from repo",
                    "text": "from repo",
                    "internal": False,
                    "created_at": datetime(2025, 1, 4, 12, tzinfo=UTC),
                    "attachments": [],
                }
            ],
            "next_cursor": "1",
        }

    async def record_message(self, **payload):
        self.record_messages.append(payload)
        return {
            "id": payload["message_id"],
            "ticket_id": payload["ticket_id"],
            "author_id": payload["author_id"],
            "author_name": payload.get("author_name"),
            "text": payload["text"],
            "internal": payload["internal"],
            "created_at": payload["created_at"],
            "attachments": payload["attachments"],
        }

    async def record_ticket_update(self, ticket_id, **payload):
        self.record_updates.append({"ticket_id": ticket_id, **payload})


@pytest.mark.asyncio
async def test_list_tickets_merges_repository(moderation_service):
    service = moderation_service
    repo = DummyTicketsRepository()

    result = await tickets.list_tickets(service, repository=repo)

    assert repo.fetch_calls, "repository was not used"
    assert all(item.priority == TicketPriority.urgent for item in result["items"])
    assert all(item.meta.get("channel") == "repo" for item in result["items"])


@pytest.mark.asyncio
async def test_add_ticket_message_uses_repository(moderation_service, moderation_data):
    service = moderation_service
    repo = DummyTicketsRepository()
    ticket_id = moderation_data["tickets"]["main"]

    dto = await tickets.add_ticket_message(
        service,
        ticket_id=ticket_id,
        body={"text": "repo", "attachments": []},
        author_id="user",
        repository=repo,
    )

    assert repo.record_messages and repo.record_updates
    assert dto.id == repo.record_messages[0]["message_id"]
    assert dto.text == "repo"


@pytest.mark.asyncio
async def test_list_ticket_messages_prefers_repository(
    moderation_service, moderation_data
):
    service = moderation_service
    repo = DummyTicketsRepository()
    ticket_id = moderation_data["tickets"]["main"]

    result = await tickets.list_ticket_messages(
        service,
        ticket_id,
        limit=5,
        cursor=None,
        repository=repo,
    )

    assert repo.list_calls == [(ticket_id, 5, None)]
    assert result["items"][0].text == "from repo"
    assert result["next_cursor"] == "1"


@pytest.mark.asyncio
async def test_get_ticket_merges_repository(moderation_service, moderation_data):
    service = moderation_service
    repo = DummyTicketsRepository()
    ticket_id = moderation_data["tickets"]["main"]

    dto = await tickets.get_ticket(service, ticket_id, repository=repo)

    assert dto.status == TicketStatus.waiting
    assert dto.meta.get("channel") == "repo"
