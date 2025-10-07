from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from domains.platform.moderation.application.common import isoformat_utc
from domains.platform.moderation.application.tickets import commands as ticket_commands
from domains.platform.moderation.application.tickets import queries as ticket_queries
from domains.platform.moderation.domain.dtos import (
    TicketMessageDTO,
    TicketPriority,
    TicketStatus,
)
from domains.platform.moderation.domain.records import TicketMessageRecord, TicketRecord
from domains.platform.moderation.application import tickets


class StubRepo:
    def __init__(self) -> None:
        self.recorded_messages: list[dict[str, Any]] = []
        self.recorded_updates: list[dict[str, Any]] = []

    async def fetch_many(self, ticket_ids):
        ids = list(ticket_ids)
        return {
            tid: {
                "status": "progress",
                "priority": "high",
                "assignee_id": "agent",
                "updated_at": datetime(2025, 1, 3, tzinfo=UTC),
                "last_message_at": datetime(2025, 1, 3, 12, tzinfo=UTC),
                "unread_count": 1,
                "meta": {"source": "repo"},
            }
            for tid in ids
        }

    async def fetch_ticket(self, ticket_id: str):
        if ticket_id != "t1":
            return None
        return {
            "status": "waiting",
            "priority": "low",
            "assignee_id": "agent",
            "updated_at": datetime(2025, 1, 4, tzinfo=UTC),
            "last_message_at": datetime(2025, 1, 4, 12, tzinfo=UTC),
            "unread_count": 2,
            "meta": {"source": "repo"},
        }

    async def list_messages(self, ticket_id: str, *, limit: int, cursor: str | None):
        return {
            "items": [
                {
                    "id": "msg-db",
                    "ticket_id": ticket_id,
                    "author_id": "agent",
                    "author_name": "Agent",
                    "text": "from repo",
                    "attachments": [],
                    "internal": False,
                    "created_at": datetime(2025, 1, 4, tzinfo=UTC),
                }
            ],
            "next_cursor": "1",
        }

    async def record_message(self, **payload: Any):
        self.recorded_messages.append(payload)
        return {
            "id": payload.get("message_id", "m-db"),
            "ticket_id": payload.get("ticket_id", "t-db"),
            "author_id": payload.get("author_id", "system"),
            "text": payload.get("text", ""),
            "attachments": payload.get("attachments", []),
            "internal": payload.get("internal", False),
            "author_name": payload.get("author_name"),
            "created_at": payload.get("created_at"),
        }

    async def record_ticket_update(self, ticket_id: str, **payload: Any) -> None:
        self.recorded_updates.append({"ticket_id": ticket_id, **payload})


class StubService:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._tickets = {
            "t1": TicketRecord(
                id="t1",
                title="Issue",
                priority=TicketPriority.normal,
                author_id="user-1",
                assignee_id="mod-1",
                status=TicketStatus.new,
                created_at=datetime(2025, 1, 1, tzinfo=UTC),
                updated_at=datetime(2025, 1, 1, tzinfo=UTC),
                last_message_at=None,
                unread_count=0,
                message_ids=["m1"],
                meta={},
            )
        }
        self._ticket_messages = {
            "m1": TicketMessageRecord(
                id="m1",
                ticket_id="t1",
                author_id="user-1",
                text="Hello",
                attachments=[],
                internal=False,
                author_name="User",
                created_at=datetime(2025, 1, 1, tzinfo=UTC),
            )
        }
        self._reports: dict[str, dict[str, Any]] = {}

    def _now(self) -> datetime:
        return datetime(2025, 1, 2, tzinfo=UTC)

    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}-generated"

    def _ticket_to_dto(self, ticket: TicketRecord) -> dict[str, Any]:
        return {
            "id": ticket.id,
            "title": ticket.title,
            "priority": ticket.priority,
            "author_id": ticket.author_id,
            "assignee_id": ticket.assignee_id,
            "status": ticket.status,
            "created_at": isoformat_utc(ticket.created_at),
            "updated_at": isoformat_utc(ticket.updated_at),
            "last_message_at": isoformat_utc(ticket.last_message_at),
            "unread_count": ticket.unread_count,
            "meta": dict(ticket.meta),
        }

    def _ticket_message_to_dto(self, message: TicketMessageRecord) -> TicketMessageDTO:
        return TicketMessageDTO(
            id=message.id,
            ticket_id=message.ticket_id,
            author_id=message.author_id,
            text=message.text,
            attachments=list(message.attachments),
            internal=message.internal,
            author_name=message.author_name,
            created_at=isoformat_utc(message.created_at),
        )


def _run(awaitable):
    return asyncio.run(awaitable)  # type: ignore[arg-type]


def test_list_tickets_returns_payload() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(ticket_queries.list_tickets(service, limit=10, repository=repo))
    assert result["items"] and result["items"][0].id == "t1"
    assert result["items"][0].meta.get("source") == "repo"


def test_get_ticket_returns_dto() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(ticket_queries.get_ticket(service, "t1", repository=repo))
    assert result.id == "t1"
    assert result.meta.get("source") == "repo"


def test_list_ticket_messages_returns_payload() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(
        ticket_queries.list_ticket_messages(
            service,
            "t1",
            limit=5,
            repository=repo,
        )
    )
    assert result["items"] and result["items"][0].text == "from repo"
    assert result["next_cursor"] == "1"


def test_add_update_escalate_ticket() -> None:
    service = StubService()
    repo = StubRepo()
    result_add = _run(
        ticket_commands.add_ticket_message(
            service,
            "t1",
            {"text": "Ping"},
            author_id="user-2",
            author_name="Another",
            repository=repo,
        )
    )
    assert result_add.ticket_id == "t1"

    with pytest.raises(KeyError):
        _run(ticket_commands.update_ticket(service, "missing", {}, repository=repo))

    with pytest.raises(ValueError):
        _run(
            ticket_commands.update_ticket(
                service,
                "t1",
                {"status": "bad"},
                repository=repo,
            )
        )

    result_update = _run(
        ticket_commands.update_ticket(
            service,
            "t1",
            {"status": "progress"},
            repository=repo,
        )
    )
    assert result_update["status"] == "progress"

    result_escalate = _run(
        ticket_commands.escalate_ticket(
            service,
            "t1",
            {},
            actor_id="mod",
            repository=repo,
        )
    )
    assert result_escalate["escalated"] is True


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
