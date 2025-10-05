from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from ...domain.dtos import TicketDTO, TicketMessageDTO, TicketPriority, TicketStatus
from ...domain.records import TicketMessageRecord, TicketRecord
from ..common import paginate, parse_iso_datetime, resolve_iso
from ..presenters.dto_builders import ticket_message_to_dto, ticket_to_dto
from .presenter import (
    build_messages_response,
    build_tickets_list_response,
    merge_ticket_with_db,
    message_from_db,
)
from .repository import TicketsRepository

ResolverFunc = Callable[[str], TicketMessageRecord | None]

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService


def _matches_filters(
    ticket: TicketRecord,
    *,
    status_filter: str | None,
    priority_filter: str | None,
    author_filter: str | None,
    assignee_filter: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
) -> bool:
    if status_filter and ticket.status.value.lower() != status_filter:
        return False
    if priority_filter and ticket.priority.value.lower() != priority_filter:
        return False
    if author_filter and ticket.author_id != author_filter:
        return False
    if assignee_filter and ticket.assignee_id != assignee_filter:
        return False
    created_at = ticket.created_at or datetime.min.replace(tzinfo=UTC)
    if created_from and created_at < created_from:
        return False
    if created_to and created_at > created_to:
        return False
    return True


def _to_ticket_dto(
    service: PlatformModerationService, ticket: TicketRecord
) -> TicketDTO:
    resolve = getattr(service, "_ticket_messages", None)
    if isinstance(resolve, dict):

        def lookup(message_id: str) -> TicketMessageRecord | None:
            return resolve.get(message_id)

        resolver: ResolverFunc = lookup
    else:
        raw_resolver = getattr(service, "_resolve_ticket_message", None)
        if callable(raw_resolver):
            resolver = cast(ResolverFunc, raw_resolver)
        else:

            def _fallback(_mid: str) -> TicketMessageRecord | None:
                return None

            resolver = _fallback
    return ticket_to_dto(
        ticket,
        resolve_message=resolver,
        iso=resolve_iso(service),
    )


def _to_message_dto(
    service: PlatformModerationService, message: TicketMessageRecord
) -> TicketMessageDTO:
    return ticket_message_to_dto(message, iso=resolve_iso(service))


async def list_tickets(
    service: PlatformModerationService,
    *,
    status: TicketStatus | str | None = None,
    priority: TicketPriority | str | None = None,
    author: str | None = None,
    assignee: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    repository: TicketsRepository | None = None,
) -> dict[str, Any]:
    async with service._lock:
        tickets = list(service._tickets.values())

    status_filter = (
        status.value
        if isinstance(status, TicketStatus)
        else (str(status).lower() if status else None)
    )
    priority_filter = (
        priority.value
        if isinstance(priority, TicketPriority)
        else (str(priority).lower() if priority else None)
    )
    author_filter = author
    assignee_filter = assignee
    created_from = parse_iso_datetime(date_from)
    created_to = parse_iso_datetime(date_to)

    filtered = [
        ticket
        for ticket in tickets
        if _matches_filters(
            ticket,
            status_filter=status_filter,
            priority_filter=priority_filter,
            author_filter=author_filter,
            assignee_filter=assignee_filter,
            created_from=created_from,
            created_to=created_to,
        )
    ]

    filtered.sort(
        key=lambda t: t.updated_at or t.created_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    chunk, next_cursor = paginate(filtered, limit, cursor)
    dtos = [_to_ticket_dto(service, t) for t in chunk]

    if repository is not None and dtos:
        db_map = await repository.fetch_many(dto.id for dto in dtos)
        dtos = [merge_ticket_with_db(dto, db_map.get(dto.id)) for dto in dtos]

    return build_tickets_list_response(dtos, next_cursor)


async def get_ticket(
    service: PlatformModerationService,
    ticket_id: str,
    *,
    repository: TicketsRepository | None = None,
) -> TicketDTO:
    async with service._lock:
        ticket = service._tickets.get(ticket_id)
        if not ticket:
            raise KeyError(ticket_id)
        dto = _to_ticket_dto(service, ticket)
    if repository is None:
        return dto
    db_info = await repository.fetch_ticket(ticket_id)
    return merge_ticket_with_db(dto, db_info)


async def list_ticket_messages(
    service: PlatformModerationService,
    ticket_id: str,
    *,
    limit: int = 50,
    cursor: str | None = None,
    repository: TicketsRepository | None = None,
) -> dict[str, Any]:
    async with service._lock:
        ticket = service._tickets.get(ticket_id)
        if not ticket:
            raise KeyError(ticket_id)
        messages = [
            service._ticket_messages[mid]
            for mid in ticket.message_ids
            if mid in service._ticket_messages
        ]

    messages.sort(
        key=lambda m: m.created_at or datetime.min.replace(tzinfo=UTC), reverse=True
    )
    chunk, next_cursor = paginate(messages, limit, cursor)
    dtos = [_to_message_dto(service, m) for m in chunk]

    if repository is not None:
        snapshot = await repository.list_messages(ticket_id, limit=limit, cursor=cursor)
        if snapshot.get("items"):
            db_messages = [message_from_db(row) for row in snapshot["items"]]
            # prefer DB messages when available
            return build_messages_response(db_messages, snapshot.get("next_cursor"))

    return build_messages_response(dtos, next_cursor)


__all__ = [
    "get_ticket",
    "list_ticket_messages",
    "list_tickets",
]
