from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from domains.platform.moderation.application.common import isoformat_utc
from domains.platform.moderation.application.tickets.exceptions import (
    ModerationTicketError,
)
from domains.platform.moderation.application.tickets.repository import TicketsRepository
from domains.platform.moderation.application.tickets.use_cases import (
    UseCaseResult,
    add_ticket_message,
    escalate_ticket,
    get_ticket,
    list_ticket_messages,
    list_tickets,
    update_ticket,
)
from domains.platform.moderation.domain.dtos import (
    TicketMessageDTO,
    TicketPriority,
    TicketStatus,
)
from domains.platform.moderation.domain.records import TicketMessageRecord, TicketRecord


class StubRepo(TicketsRepository):
    def __init__(self) -> None:  # type: ignore[no-untyped-def]
        self._engine = None
        self.recorded_messages: list[dict[str, Any]] = []
        self.recorded_updates: list[dict[str, Any]] = []

    async def list_tickets(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        return {"items": [], "next_cursor": None}

    async def list_messages(self, ticket_id: str, *, limit: int, cursor: str | None) -> dict[str, Any]:  # type: ignore[override]
        return {"items": [], "next_cursor": None}

    async def fetch_many(self, ticket_ids):  # type: ignore[override]
        return {}

    async def fetch_ticket(self, ticket_id: str):  # type: ignore[override]
        return None

    async def record_message(self, **payload: Any) -> dict[str, Any] | None:  # type: ignore[override]
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

    async def record_ticket_update(self, ticket_id: str, **payload: Any) -> None:  # type: ignore[override]
        entry = {"ticket_id": ticket_id, **payload}
        self.recorded_updates.append(entry)


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
    result = _run(list_tickets(service, repo, limit=10))
    assert isinstance(result, UseCaseResult)
    assert result.payload["items"], "expected non-empty items"


def test_get_ticket_returns_dto() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(get_ticket(service, repo, "t1"))
    assert result.payload["id"] == "t1"


def test_list_ticket_messages_returns_payload() -> None:
    service = StubService()
    repo = StubRepo()
    result = _run(list_ticket_messages(service, repo, "t1", limit=5))
    assert isinstance(result.payload.get("items"), list)


def test_add_update_escalate_ticket() -> None:
    service = StubService()
    repo = StubRepo()
    result_add = _run(
        add_ticket_message(
            service,
            repo,
            ticket_id="t1",
            payload={"text": "Ping"},
            author_id="user-2",
            author_name="Another",
        )
    )
    assert result_add.payload["ticket_id"] == "t1"

    with pytest.raises(ModerationTicketError) as exc:
        _run(update_ticket(service, repo, ticket_id="missing", payload={}))
    assert exc.value.code == "ticket_not_found"

    with pytest.raises(ModerationTicketError) as exc:
        _run(update_ticket(service, repo, ticket_id="t1", payload={"status": "bad"}))
    assert exc.value.code == "invalid_ticket_status"

    result_update = _run(
        update_ticket(service, repo, ticket_id="t1", payload={"status": "progress"})
    )
    assert result_update.payload["status"] == "progress"

    result_escalate = _run(
        escalate_ticket(service, repo, ticket_id="t1", payload={}, actor_id="mod")
    )
    assert result_escalate.payload["escalated"] is True
