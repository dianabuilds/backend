from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..service import PlatformModerationService

from ...domain.dtos import ContentSummary, ContentType
from .exceptions import ModerationContentError
from .queries import list_content as list_content_query
from .repository import ContentRepository, create_repository

__all__ = [
    "ContentRepository",
    "UseCaseResult",
    "create_repository",
    "decide_content",
    "edit_content",
    "get_content",
    "list_content",
    "list_queue",
]

list_content = list_content_query


def __getattr__(name: str):  # pragma: no cover - compatibility export
    if name == "UseCaseResult":
        from .use_cases import UseCaseResult as _UseCaseResult

        globals()["UseCaseResult"] = _UseCaseResult
        return _UseCaseResult
    raise AttributeError(name)


def _use_cases():
    from . import use_cases

    return use_cases


def _resolve_repository(repository: ContentRepository | None) -> ContentRepository:
    return repository if repository is not None else ContentRepository(None)


async def list_queue(
    repository: ContentRepository | None,
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
) -> dict[str, Any]:
    repo = _resolve_repository(repository)
    use_cases = _use_cases()
    result = await use_cases.list_queue(
        repo,
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
    return result.payload


async def get_content(
    service: PlatformModerationService,
    content_id: str,
    *,
    repository: ContentRepository | None = None,
):
    use_cases = _use_cases()
    try:
        result = await use_cases.get_content(
            service,
            content_id,
            repository=repository,
        )
    except ModerationContentError as exc:
        raise KeyError(content_id) from exc
    payload = result.payload
    if isinstance(payload, ContentSummary):
        return payload
    if isinstance(payload, dict):
        data = dict(payload)
        data.pop("moderation_status", None)
        return ContentSummary.model_validate(data)
    data = dict(payload)
    data.pop("moderation_status", None)
    return ContentSummary.model_validate(data)


async def decide_content(
    service: PlatformModerationService,
    content_id: str,
    body: Mapping[str, Any],
    *,
    actor_id: str | None = None,
    repository: ContentRepository | None = None,
) -> dict[str, Any]:
    repo = _resolve_repository(repository)
    use_cases = _use_cases()
    try:
        result = await use_cases.decide_content(
            service,
            repo,
            content_id=content_id,
            payload=dict(body),
            actor_id=actor_id,
        )
    except ModerationContentError as exc:
        raise KeyError(content_id) from exc
    return result.payload


async def edit_content(
    service: PlatformModerationService,
    content_id: str,
    patch: Mapping[str, Any],
) -> dict[str, Any]:
    use_cases = _use_cases()
    try:
        result = await use_cases.edit_content(
            service,
            content_id=content_id,
            payload=dict(patch),
        )
    except ModerationContentError as exc:
        raise KeyError(content_id) from exc
    return result.payload
