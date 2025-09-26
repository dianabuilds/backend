from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException

from ..dtos import TicketDTO, TicketMessageDTO, TicketPriority, TicketStatus
from ..rbac import require_scopes

router = APIRouter(prefix="/tickets", tags=["moderation-tickets"])


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
    # No SQL storage for moderation tickets; return empty list for real-data mode
    return {"items": [], "next_cursor": None}


@router.get(
    "/{ticket_id}",
    response_model=TicketDTO,
    dependencies=[Depends(require_scopes("moderation:tickets:read"))],
)
async def get_ticket(ticket_id: str, container=Depends(get_container)) -> TicketDTO:
    svc = container.platform_moderation.service
    try:
        return await svc.get_ticket(ticket_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticket_not_found") from exc


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
    svc = container.platform_moderation.service
    try:
        return await svc.list_ticket_messages(ticket_id, limit=limit, cursor=cursor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticket_not_found") from exc


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
    svc = container.platform_moderation.service
    try:
        return await svc.add_ticket_message(
            ticket_id,
            body,
            author_id=body.get("author_id", "system"),
            author_name=body.get("author_name"),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticket_not_found") from exc


@router.patch(
    "/{ticket_id}",
    dependencies=[Depends(require_scopes("moderation:tickets:read"))],
)
async def update_ticket(
    ticket_id: str, body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        return await svc.update_ticket(ticket_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticket_not_found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/{ticket_id}/escalate",
    dependencies=[Depends(require_scopes("moderation:tickets:comment:write"))],
)
async def escalate_ticket(
    ticket_id: str,
    body: dict[str, Any] | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        return await svc.escalate_ticket(
            ticket_id, body or {}, actor_id=(body or {}).get("actor_id")
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ticket_not_found") from exc


__all__ = ["router"]
