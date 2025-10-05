from __future__ import annotations

import logging
from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException, Query

from ..api.rbac import require_scopes
from ..application.content import (
    ContentRepository,
    create_repository,
)
from ..application.content import (
    commands as content_commands,
)
from ..application.content import (
    queries as content_queries,
)
from ..dtos import ContentSummary, ContentType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["moderation-content"])


def _build_repository(container) -> ContentRepository:
    return create_repository(container.settings)


@router.get(
    "",
    dependencies=[Depends(require_scopes("moderation:content:read"))],
)
async def list_queue(
    type: ContentType | None = None,  # noqa: A002
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
    return await content_queries.list_queue(
        repository,
        content_type=type,
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
        return await content_queries.get_content(
            svc,
            content_id,
            repository=repository,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content_not_found") from exc


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
        result = await content_commands.decide_content(
            svc,
            content_id,
            body,
            actor_id=body.get("actor"),
            repository=repository,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content_not_found") from exc

    response = {"content_id": content_id, **result}
    db_record = response.pop("db_record", None)
    if db_record:
        response["moderation_status"] = db_record.get("status")
        if db_record.get("history_entry"):
            response.setdefault("decision", result.get("decision", {}))
            response["decision"]["decided_at"] = response["decision"].get(
                "decided_at"
            ) or db_record["history_entry"].get("decided_at")
            response["decision"]["status"] = db_record["history_entry"].get("status")
        response["db_state"] = db_record
    return response


@router.patch(
    "/{content_id}",
    dependencies=[Depends(require_scopes("moderation:content:edit:write"))],
)
async def edit_content(
    content_id: str, body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        return await content_commands.edit_content(svc, content_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content_not_found") from exc


__all__ = ["router"]
