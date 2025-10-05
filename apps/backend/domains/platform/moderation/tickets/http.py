from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException

from ..api.rbac import require_scopes
from ..application.tickets.exceptions import ModerationTicketError
from ..application.tickets.repository import TicketsRepository, create_repository
from ..application.tickets.use_cases import (
    UseCaseResult,
)
from ..application.tickets.use_cases import (
    add_ticket_message as add_ticket_message_use_case,
)
from ..application.tickets.use_cases import (
    escalate_ticket as escalate_ticket_use_case,
)
from ..application.tickets.use_cases import (
    get_ticket as get_ticket_use_case,
)
from ..application.tickets.use_cases import (
    list_ticket_messages as list_ticket_messages_use_case,
)
from ..application.tickets.use_cases import (
    list_tickets as list_tickets_use_case,
)
from ..application.tickets.use_cases import (
    update_ticket as update_ticket_use_case,
)
from ..dtos import TicketDTO, TicketMessageDTO, TicketPriority, TicketStatus

router = APIRouter(prefix="/tickets", tags=["moderation-tickets"])


def _build_repository(container) -> TicketsRepository:
    return create_repository(container.settings)


def _apply(result: UseCaseResult) -> dict[str, Any]:
    return result.payload


def _raise_ticket_error(error: ModerationTicketError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.code) from error

@router.get("", dependencies=[Depends(require_scopes("moderation:tickets:read"))])
async def list_tickets(
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    author: str | None = None,
    assignee: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    repository = _build_repository(container)
    result = await list_tickets_use_case(
        container.platform_moderation.service,
        repository,
        status=status,
        priority=priority,
        author=author,
        assignee=assignee,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )
    return result.payload

@router.get(
    "/{ticket_id}",
    response_model=TicketDTO,
    dependencies=[Depends(require_scopes("moderation:tickets:read"))],
)
async def get_ticket(ticket_id: str, container=Depends(get_container)) -> TicketDTO:
    repository = _build_repository(container)
    try:
        result = await get_ticket_use_case(
            container.platform_moderation.service,
            repository,
            ticket_id,
        )
    except ModerationTicketError as error:
        _raise_ticket_error(error)
    return TicketDTO.model_validate(result.payload)

@router.get(
    "/{ticket_id}/messages",
    dependencies=[Depends(require_scopes("moderation:tickets:read"))],
)
async def list_messages(
    ticket_id: str,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    repository = _build_repository(container)
    try:
        result = await list_ticket_messages_use_case(
            container.platform_moderation.service,
            repository,
            ticket_id,
            limit=limit,
            cursor=cursor,
        )
    except ModerationTicketError as error:
        _raise_ticket_error(error)
    return result.payload

@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageDTO,
    dependencies=[Depends(require_scopes("moderation:tickets:comment:write"))],
)
async def add_message(
    ticket_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> TicketMessageDTO:
    repository = _build_repository(container)
    try:
        result = await add_ticket_message_use_case(
            container.platform_moderation.service,
            repository,
            ticket_id=ticket_id,
            payload=body,
            author_id=body.get("author_id", "system"),
            author_name=body.get("author_name"),
        )
    except ModerationTicketError as error:
        _raise_ticket_error(error)
    return TicketMessageDTO.model_validate(result.payload)

@router.patch(
    "/{ticket_id}",
    dependencies=[Depends(require_scopes("moderation:tickets:read"))],
)
async def update_ticket(
    ticket_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> dict[str, Any]:
    repository = _build_repository(container)
    try:
        result = await update_ticket_use_case(
            container.platform_moderation.service,
            repository,
            ticket_id=ticket_id,
            payload=body,
        )
    except ModerationTicketError as error:
        _raise_ticket_error(error)
    return result.payload

@router.post(
    "/{ticket_id}/escalate",
    dependencies=[Depends(require_scopes("moderation:tickets:comment:write"))],
)
async def escalate_ticket(
    ticket_id: str,
    body: dict[str, Any] | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    repository = _build_repository(container)
    try:
        result = await escalate_ticket_use_case(
            container.platform_moderation.service,
            repository,
            ticket_id=ticket_id,
            payload=body,
            actor_id=(body or {}).get("actor_id"),
        )
    except ModerationTicketError as error:
        _raise_ticket_error(error)
    return result.payload


__all__ = ["router"]
