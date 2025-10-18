from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from ...domain.dtos import TicketDTO, TicketMessageDTO, TicketPriority, TicketStatus
from ..common import isoformat_utc
from ..presenters import build_list_response, field, merge_metadata, merge_model


def _coerce_status(value: Any, fallback: TicketStatus) -> TicketStatus:
    if isinstance(value, TicketStatus):
        return value
    try:
        return TicketStatus(str(value))
    except (TypeError, ValueError):
        return fallback


def _coerce_priority(value: Any, fallback: TicketPriority) -> TicketPriority:
    if isinstance(value, TicketPriority):
        return value
    try:
        return TicketPriority(str(value))
    except (TypeError, ValueError):
        return fallback


def merge_ticket_with_db(
    ticket: TicketDTO, db_info: Mapping[str, object] | None
) -> TicketDTO:
    merged = merge_model(
        ticket,
        db_info,
        field_map={
            "status": field(
                "status",
                transform=lambda value: _coerce_status(value, ticket.status),
            ),
            "priority": field(
                "priority",
                transform=lambda value: _coerce_priority(value, ticket.priority),
            ),
            "assignee_id": field("assignee_id"),
            "updated_at": field("updated_at", transform=isoformat_utc),
            "last_message_at": field("last_message_at", transform=isoformat_utc),
            "unread_count": field("unread_count"),
            "meta": field(
                "meta",
                transform=lambda value: merge_metadata(
                    ticket.meta, value if isinstance(value, Mapping) else {}
                ),
            ),
        },
    )
    return cast(TicketDTO, merged)


def build_tickets_list_response(
    items: list[TicketDTO], next_cursor: str | None
) -> dict[str, Any]:
    return build_list_response(items, next_cursor=next_cursor)


def build_messages_response(
    messages: list[TicketMessageDTO], next_cursor: str | None
) -> dict[str, Any]:
    return build_list_response(messages, next_cursor=next_cursor)


def message_from_db(payload: dict[str, Any]) -> TicketMessageDTO:
    return TicketMessageDTO(
        id=payload["id"],
        ticket_id=payload["ticket_id"],
        author_id=payload.get("author_id", "system"),
        text=payload.get("text", ""),
        attachments=list(payload.get("attachments", [])),
        internal=bool(payload.get("internal", False)),
        author_name=payload.get("author_name"),
        created_at=isoformat_utc(payload.get("created_at")),
    )


__all__ = [
    "build_messages_response",
    "build_tickets_list_response",
    "merge_ticket_with_db",
    "message_from_db",
]
