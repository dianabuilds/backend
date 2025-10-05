from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict

from ...domain.dtos import TicketMessageDTO, TicketPriority, TicketStatus
from ...domain.records import TicketMessageRecord
from ..common import isoformat_utc, parse_iso_datetime, resolve_iso
from ..presenters.dto_builders import ticket_message_to_dto
from .presenter import message_from_db
from .repository import TicketsRepository

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService


logger = logging.getLogger(__name__)


class TicketSnapshot(TypedDict):
    status: str
    priority: str
    assignee_id: str | None
    updated_at: datetime | None
    last_message_at: datetime | None
    unread_count: int
    meta: dict[str, Any]


class MessageSnapshot(TypedDict):
    message_id: str
    ticket_id: str
    author_id: str
    author_name: str | None
    text: str
    internal: bool
    created_at: datetime | None
    attachments: list[dict[str, Any]]


async def add_ticket_message(
    service: PlatformModerationService,
    ticket_id: str,
    body: dict[str, Any],
    *,
    author_id: str,
    author_name: str | None = None,
    repository: TicketsRepository | None = None,
) -> TicketMessageDTO:
    async with service._lock:
        ticket = service._tickets.get(ticket_id)
        if not ticket:
            raise KeyError(ticket_id)
        message = TicketMessageRecord(
            id=service._generate_id("msg"),
            ticket_id=ticket.id,
            author_id=author_id,
            text=str(body.get("text") or ""),
            attachments=[dict(a) for a in body.get("attachments") or []],
            internal=bool(body.get("internal") or False),
            author_name=author_name or body.get("author_name"),
            created_at=parse_iso_datetime(body.get("created_at")) or service._now(),
        )
        service._ticket_messages[message.id] = message
        ticket.message_ids.append(message.id)
        ticket.last_message_at = message.created_at
        ticket.updated_at = message.created_at
        if body.get("increment_unread", True) and not message.internal:
            ticket.unread_count = max(ticket.unread_count, 0) + 1
        dto = ticket_message_to_dto(message, iso=resolve_iso(service))
        ticket_snapshot: TicketSnapshot = {
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "assignee_id": ticket.assignee_id,
            "updated_at": ticket.updated_at,
            "last_message_at": ticket.last_message_at,
            "unread_count": ticket.unread_count,
            "meta": dict(ticket.meta),
        }
        message_snapshot: MessageSnapshot = {
            "message_id": message.id,
            "ticket_id": message.ticket_id,
            "author_id": message.author_id,
            "author_name": message.author_name,
            "text": message.text,
            "internal": message.internal,
            "created_at": message.created_at,
            "attachments": [dict(a) for a in message.attachments],
        }

    if repository is not None:
        status_snapshot: str = ticket_snapshot["status"]
        priority_snapshot: str = ticket_snapshot["priority"]
        assignee_snapshot: str | None = ticket_snapshot["assignee_id"]
        updated_snapshot: datetime | None = ticket_snapshot["updated_at"]
        last_message_snapshot: datetime | None = ticket_snapshot["last_message_at"]
        unread_snapshot: int = ticket_snapshot["unread_count"]
        meta_snapshot: dict[str, Any] = ticket_snapshot["meta"]
        persisted = await repository.record_message(
            message_id=message_snapshot["message_id"],
            ticket_id=message_snapshot["ticket_id"],
            author_id=message_snapshot["author_id"],
            text=message_snapshot["text"],
            created_at=message_snapshot["created_at"],
            internal=message_snapshot["internal"],
            attachments=message_snapshot["attachments"],
            author_name=message_snapshot["author_name"],
        )
        await repository.record_ticket_update(
            ticket_id,
            status=status_snapshot,
            priority=priority_snapshot,
            assignee_id=assignee_snapshot,
            updated_at=updated_snapshot,
            last_message_at=last_message_snapshot,
            unread_count=unread_snapshot,
            meta=meta_snapshot,
        )
        if persisted:
            return message_from_db(persisted)
    return dto


async def update_ticket(
    service: PlatformModerationService,
    ticket_id: str,
    patch: dict[str, Any],
    *,
    repository: TicketsRepository | None = None,
) -> dict[str, Any]:
    async with service._lock:
        ticket = service._tickets.get(ticket_id)
        if not ticket:
            raise KeyError(ticket_id)
        if "status" in patch and patch["status"] is not None:
            try:
                ticket.status = TicketStatus(str(patch["status"]))
            except ValueError as exc:
                raise ValueError("invalid_ticket_status") from exc
        if "priority" in patch and patch["priority"] is not None:
            try:
                ticket.priority = TicketPriority(str(patch["priority"]))
            except ValueError as exc:
                raise ValueError("invalid_ticket_priority") from exc
        if "assignee_id" in patch:
            ticket.assignee_id = patch["assignee_id"]
        if "unread_count" in patch:
            try:
                ticket.unread_count = max(0, int(patch["unread_count"]))
            except (TypeError, ValueError) as exc:
                logger.debug(
                    "Ignoring invalid unread_count %r for ticket %s: %s",
                    patch.get("unread_count"),
                    ticket_id,
                    exc,
                )
                ticket.unread_count = max(ticket.unread_count, 0)
        if "meta" in patch and patch["meta"]:
            ticket.meta.update(dict(patch["meta"]))
        ticket.updated_at = service._now()
        response = {
            "ticket_id": ticket_id,
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "assignee_id": ticket.assignee_id,
        }
        ticket_snapshot: TicketSnapshot = {
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "assignee_id": ticket.assignee_id,
            "updated_at": ticket.updated_at,
            "last_message_at": ticket.last_message_at,
            "unread_count": ticket.unread_count,
            "meta": dict(ticket.meta),
        }

    if repository is not None:
        status_snapshot: str = ticket_snapshot["status"]
        priority_snapshot: str = ticket_snapshot["priority"]
        assignee_snapshot: str | None = ticket_snapshot["assignee_id"]
        updated_snapshot: datetime | None = ticket_snapshot["updated_at"]
        last_message_snapshot: datetime | None = ticket_snapshot["last_message_at"]
        unread_snapshot: int = ticket_snapshot["unread_count"]
        meta_snapshot: dict[str, Any] = ticket_snapshot["meta"]
        await repository.record_ticket_update(
            ticket_id,
            status=status_snapshot,
            priority=priority_snapshot,
            assignee_id=assignee_snapshot,
            updated_at=updated_snapshot,
            last_message_at=last_message_snapshot,
            unread_count=unread_snapshot,
            meta=meta_snapshot,
        )
    return response


async def escalate_ticket(
    service: PlatformModerationService,
    ticket_id: str,
    payload: dict[str, Any] | None = None,
    *,
    actor_id: str | None = None,
    repository: TicketsRepository | None = None,
) -> dict[str, Any]:
    async with service._lock:
        ticket = service._tickets.get(ticket_id)
        if not ticket:
            raise KeyError(ticket_id)
        ticket.status = TicketStatus.escalated
        ticket.meta.setdefault("escalations", []).append(
            {
                "actor": actor_id or "system",
                "reason": (payload or {}).get("reason"),
                "at": isoformat_utc(service._now()),
            }
        )
        ticket.updated_at = service._now()
        response = {
            "ticket_id": ticket_id,
            "status": ticket.status.value,
            "escalated": True,
        }
        ticket_snapshot: TicketSnapshot = {
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "assignee_id": ticket.assignee_id,
            "updated_at": ticket.updated_at,
            "last_message_at": ticket.last_message_at,
            "unread_count": ticket.unread_count,
            "meta": dict(ticket.meta),
        }

    if repository is not None:
        status_snapshot: str = ticket_snapshot["status"]
        priority_snapshot: str = ticket_snapshot["priority"]
        assignee_snapshot: str | None = ticket_snapshot["assignee_id"]
        updated_snapshot: datetime | None = ticket_snapshot["updated_at"]
        last_message_snapshot: datetime | None = ticket_snapshot["last_message_at"]
        unread_snapshot: int = ticket_snapshot["unread_count"]
        meta_snapshot: dict[str, Any] = ticket_snapshot["meta"]
        await repository.record_ticket_update(
            ticket_id,
            status=status_snapshot,
            priority=priority_snapshot,
            assignee_id=assignee_snapshot,
            updated_at=updated_snapshot,
            last_message_at=last_message_snapshot,
            unread_count=unread_snapshot,
            meta=meta_snapshot,
        )
    return response


__all__ = [
    "add_ticket_message",
    "escalate_ticket",
    "update_ticket",
]
