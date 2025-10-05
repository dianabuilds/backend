from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.backend import get_container

from ...application.content.exceptions import ModerationContentError
from ...application.content.repository import ContentRepository, create_repository
from ...application.content.use_cases import (
    UseCaseResult,
)
from ...application.content.use_cases import (
    decide_content as decide_content_use_case,
)
from ...application.content.use_cases import (
    edit_content as edit_content_use_case,
)
from ...application.content.use_cases import (
    get_content as get_content_use_case,
)
from ...application.content.use_cases import (
    list_queue as list_queue_use_case,
)
from ...dtos import ContentSummary, ContentType
from ..rbac import require_scopes

router = APIRouter(prefix="/content", tags=["moderation-content"])


def _build_repository(container) -> ContentRepository:
    return create_repository(container.settings)


def _apply(result: UseCaseResult, *, http_raise: bool = False) -> dict[str, Any]:
    if http_raise and result.status_code >= 400:
        raise HTTPException(status_code=result.status_code, detail=result.payload)
    return result.payload


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
) -> dict[str, Any]:
    repository = _build_repository(container)
    try:
        result = await list_queue_use_case(
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
    return result.payload


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
        result = await get_content_use_case(
            svc,
            content_id,
            repository=repository,
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return ContentSummary.model_validate(result.payload)


@router.post(
    "/{content_id}/decision",
    dependencies=[Depends(require_scopes("moderation:content:decide:write"))],
)
async def decide_content(
    content_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    repository = _build_repository(container)
    try:
        result = await decide_content_use_case(
            svc,
            repository,
            content_id=content_id,
            payload=body,
            actor_id=body.get("actor"),
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return result.payload


@router.patch(
    "/{content_id}",
    dependencies=[Depends(require_scopes("moderation:content:edit:write"))],
)
async def edit_content(
    content_id: str, body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        result = await edit_content_use_case(
            svc,
            content_id=content_id,
            payload=body,
        )
    except ModerationContentError as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error
    return result.payload


__all__ = ["router"]
