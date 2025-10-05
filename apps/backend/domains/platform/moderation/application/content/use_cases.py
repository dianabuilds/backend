from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ...domain.dtos import ContentSummary, ContentType
from ..service import PlatformModerationService
from .exceptions import ModerationContentError
from .presenter import (
    build_queue_response,
    decorate_decision_response,
    merge_summary_with_db,
)
from .queries import content_to_summary
from .repository import ContentRepository


@dataclass(slots=True)
class UseCaseResult:
    payload: dict[str, Any]
    status_code: int = 200


async def list_queue(
    repository: ContentRepository,
    *,
    content_type: ContentType | None = None,
    status: str | None = None,
    moderation_status: str | None = None,
    ai_label: str | None = None,
    has_reports: bool | None = None,
    author_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> UseCaseResult:
    data = await repository.list_queue(
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
    items = data.get("items", [])
    summaries: list[Any] = []
    for item in items:
        if isinstance(item, ContentSummary):
            summaries.append(item)
        elif isinstance(item, Mapping):
            summaries.append(dict(item))
        else:
            summaries.append(item)
    return UseCaseResult(
        payload=build_queue_response(summaries, next_cursor=data.get("next_cursor")),
    )


async def get_content(
    service: PlatformModerationService,
    content_id: str,
    *,
    repository: ContentRepository | None = None,
) -> UseCaseResult:
    async with service._lock:
        content = service._content.get(content_id)
        if not content:
            raise ModerationContentError(code="content_not_found", status_code=404)
        summary = content_to_summary(service, content)

    db_info = await repository.load_content_details(content_id) if repository else None
    merged = merge_summary_with_db(summary, db_info)
    if hasattr(merged, "model_dump"):
        payload = merged.model_dump()
    elif isinstance(merged, dict):
        payload = dict(merged)
    else:
        payload = dict(merged)
    status_value = payload.get("meta", {}).get("moderation_status")
    if status_value and "moderation_status" not in payload:
        payload["moderation_status"] = status_value
    return UseCaseResult(payload=payload)


async def decide_content(
    service: PlatformModerationService,
    repository: ContentRepository,
    *,
    content_id: str,
    payload: Mapping[str, Any],
    actor_id: str | None,
) -> UseCaseResult:
    try:
        result = await service.decide_content(
            content_id,
            payload,
            actor_id=actor_id,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationContentError(code="content_not_found", status_code=404) from exc
    return UseCaseResult(payload=decorate_decision_response(content_id, result))


async def edit_content(
    service: PlatformModerationService,
    *,
    content_id: str,
    payload: Mapping[str, Any],
) -> UseCaseResult:
    try:
        result = await service.edit_content(content_id, payload)
    except KeyError as exc:
        raise ModerationContentError(code="content_not_found", status_code=404) from exc
    return UseCaseResult(payload=result)


__all__ = [
    "UseCaseResult",
    "decide_content",
    "edit_content",
    "get_content",
    "list_queue",
]
