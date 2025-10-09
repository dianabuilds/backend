from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.backend.app.api_gateway.routers import get_container

from ...application.content import commands as content_commands
from ...application.content import queries as content_queries
from ...application.content.exceptions import ModerationContentError
from ...application.content.presenter import (
    DecisionResponse,
    QueueResponse,
    build_queue_response,
)
from ...application.content.repository import ContentRepository, create_repository
from ...dtos import ContentSummary, ContentType
from ..rbac import require_scopes

router = APIRouter(prefix="/content", tags=["moderation-content"])


def _build_repository(container) -> ContentRepository:
    return create_repository(container.settings)


@router.get(
    "",
    dependencies=[Depends(require_scopes("moderation:content:read"))],
)
async def list_queue(
    content_type: ContentType | None = None,
    status: str | None = None,
    moderation_status: str | None = Query(default=None),
    ai_label: str | None = None,
    has_reports: bool | None = None,
    author_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> QueueResponse:
    repository = _build_repository(container)
    try:
        raw = await content_queries.list_queue(
            repository,
            content_type=content_type,
            status=status,
            moderation_status=moderation_status,
            ai_label=ai_label,
            has_reports=has_reports,
            author_id=author_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            cursor=cursor,
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return build_queue_response(
        raw.get("items", []), next_cursor=raw.get("next_cursor")
    )


@router.get(
    "/{content_id}",
    response_model=ContentSummary,
    dependencies=[Depends(require_scopes("moderation:content:read"))],
)
async def get_content(
    content_id: str, container=Depends(get_container)
) -> ContentSummary:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        summary = await content_queries.get_content(
            svc,
            content_id,
            repository=repository,
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail="content_not_found") from error

    if isinstance(summary, ContentSummary):
        return summary
    return ContentSummary.model_validate(summary)


@router.post(
    "/{content_id}/decision",
    dependencies=[Depends(require_scopes("moderation:content:decide:write"))],
)
async def decide_content(
    content_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> DecisionResponse:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        return await content_commands.decide_content(
            svc,
            content_id,
            body,
            actor_id=body.get("actor"),
            repository=repository,
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail="content_not_found") from error


@router.patch(
    "/{content_id}",
    dependencies=[Depends(require_scopes("moderation:content:edit:write"))],
)
async def edit_content(
    content_id: str, body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        return await content_commands.edit_content(
            svc,
            content_id,
            body,
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail="content_not_found") from error


__all__ = ["router"]
