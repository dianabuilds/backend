from __future__ import annotations

from typing import Any

from ...domain.dtos import TicketDTO, TicketMessageDTO, TicketPriority, TicketStatus
from ..common import isoformat_utc
from ..presenters import build_list_response, merge_metadata, merge_model


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
    ticket: TicketDTO, db_info: dict[str, Any] | None
) -> TicketDTO:
    return merge_model(
        ticket,
        db_info,
        field_map={
            "status": ("status", lambda value: _coerce_status(value, ticket.status)),
            "priority": (
                "priority",
                lambda value: _coerce_priority(value, ticket.priority),
            ),
            "assignee_id": "assignee_id",
            "updated_at": ("updated_at", isoformat_utc),
            "last_message_at": ("last_message_at", isoformat_utc),
            "unread_count": "unread_count",
            "meta": (
                "meta",
                lambda value: merge_metadata(
                    ticket.meta, value if isinstance(value, dict) else {}
                ),
            ),
        },
    )


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
