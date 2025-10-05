from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..tickets import commands as ticket_commands
from ..tickets import queries as ticket_queries
from .exceptions import ModerationTicketError
from .repository import TicketsRepository

if TYPE_CHECKING:  # pragma: no cover
    from ..service import PlatformModerationService


@dataclass(slots=True)
class UseCaseResult:
    payload: dict[str, Any]
    status_code: int = 200


def _to_payload(dto: Any) -> dict[str, Any]:
    if hasattr(dto, "model_dump"):
        return dto.model_dump()  # type: ignore[no-any-return]
    if isinstance(dto, dict):
        return dict(dto)
    raise TypeError(f"Unsupported DTO type: {type(dto)!r}")


async def list_tickets(
    service: PlatformModerationService,
    repository: TicketsRepository,
    *,
    status: Any = None,
    priority: Any = None,
    author: str | None = None,
    assignee: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> UseCaseResult:
    data = await ticket_queries.list_tickets(
        service,
        status=status,
        priority=priority,
        author=author,
        assignee=assignee,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        repository=repository,
    )
    return UseCaseResult(payload=data)


async def get_ticket(
    service: PlatformModerationService,
    repository: TicketsRepository,
    ticket_id: str,
) -> UseCaseResult:
    try:
        dto = await ticket_queries.get_ticket(
            service,
            ticket_id,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationTicketError(code="ticket_not_found", status_code=404) from exc
    return UseCaseResult(payload=_to_payload(dto))


async def list_ticket_messages(
    service: PlatformModerationService,
    repository: TicketsRepository,
    ticket_id: str,
    *,
    limit: int = 50,
    cursor: str | None = None,
) -> UseCaseResult:
    try:
        data = await ticket_queries.list_ticket_messages(
            service,
            ticket_id,
            limit=limit,
            cursor=cursor,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationTicketError(code="ticket_not_found", status_code=404) from exc
    return UseCaseResult(payload=data)


async def add_ticket_message(
    service: PlatformModerationService,
    repository: TicketsRepository,
    *,
    ticket_id: str,
    payload: Mapping[str, Any],
    author_id: str,
    author_name: str | None,
) -> UseCaseResult:
    try:
        dto = await ticket_commands.add_ticket_message(
            service,
            ticket_id,
            dict(payload),
            author_id=author_id,
            author_name=author_name,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationTicketError(code="ticket_not_found", status_code=404) from exc
    return UseCaseResult(payload=_to_payload(dto))


async def update_ticket(
    service: PlatformModerationService,
    repository: TicketsRepository,
    *,
    ticket_id: str,
    payload: Mapping[str, Any],
) -> UseCaseResult:
    try:
        data = await ticket_commands.update_ticket(
            service,
            ticket_id,
            dict(payload),
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationTicketError(code="ticket_not_found", status_code=404) from exc
    except ValueError as exc:
        raise ModerationTicketError(
            code=str(exc) or "invalid_ticket",
            status_code=400,
            message=str(exc) or "invalid ticket",
        ) from exc
    return UseCaseResult(payload=data)


async def escalate_ticket(
    service: PlatformModerationService,
    repository: TicketsRepository,
    *,
    ticket_id: str,
    payload: Mapping[str, Any] | None,
    actor_id: str | None,
) -> UseCaseResult:
    try:
        data = await ticket_commands.escalate_ticket(
            service,
            ticket_id,
            dict(payload or {}),
            actor_id=actor_id,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationTicketError(code="ticket_not_found", status_code=404) from exc
    return UseCaseResult(payload=data)


__all__ = [
    "UseCaseResult",
    "add_ticket_message",
    "escalate_ticket",
    "get_ticket",
    "list_ticket_messages",
    "list_tickets",
    "update_ticket",
]
