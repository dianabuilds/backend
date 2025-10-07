from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ...domain.dtos import ContentSummary, ContentType
from ...domain.records import ContentRecord
from ..common import isoformat_utc, paginate, parse_iso_datetime, resolve_iso
from ..presenters.dto_builders import report_to_dto
from .presenter import QueueResponse, build_queue_response, merge_summary_with_db
from .repository import ContentRepository

if TYPE_CHECKING:  # pragma: no cover
    from ..service import PlatformModerationService


def content_to_summary(
    service: PlatformModerationService, content: ContentRecord
) -> ContentSummary:
    iso = resolve_iso(service)
    reports = [
        report_to_dto(service._reports[rid], iso=iso)
        for rid in content.report_ids
        if rid in service._reports
    ]
    return ContentSummary(
        id=content.id,
        type=content.content_type,
        author_id=content.author_id,
        created_at=isoformat_utc(content.created_at),
        preview=content.preview,
        ai_labels=list(content.ai_labels),
        complaints_count=len(content.report_ids),
        status=content.status,
        moderation_history=list(content.moderation_history),
        reports=reports,
        meta=dict(content.meta),
    )


def _match_filters(
    content: ContentRecord,
    *,
    content_type: ContentType | None,
    status_filter: str | None,
    ai_label_filter: str | None,
    has_reports: bool | None,
    author_filter: str | None,
    created_from,
    created_to,
) -> bool:
    if content_type and content.content_type != content_type:
        return False
    if status_filter and content.status.value.lower() != status_filter:
        return False
    if ai_label_filter and ai_label_filter not in [
        label.lower() for label in content.ai_labels
    ]:
        return False
    if has_reports is not None:
        present = len(content.report_ids) > 0
        if bool(has_reports) != present:
            return False
    if author_filter and content.author_id != author_filter:
        return False
    if created_from and content.created_at < created_from:
        return False
    if created_to and content.created_at > created_to:
        return False
    return True


async def list_content(
    service: PlatformModerationService,
    *,
    content_type: ContentType | None = None,  # noqa: A002
    type: ContentType | None = None,  # noqa: A002
    status: str | None = None,
    ai_label: str | None = None,
    has_reports: bool | None = None,
    author_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    async with service._lock:
        items = list(service._content.values())

    status_filter = status.lower() if status else None
    ai_label_filter = ai_label.lower() if ai_label else None
    author_filter = author_id
    created_from = parse_iso_datetime(date_from)
    created_to = parse_iso_datetime(date_to)
    selected_type = content_type if content_type is not None else type

    filtered = [
        content
        for content in items
        if _match_filters(
            content,
            content_type=selected_type,
            status_filter=status_filter,
            ai_label_filter=ai_label_filter,
            has_reports=has_reports,
            author_filter=author_filter,
            created_from=created_from,
            created_to=created_to,
        )
    ]

    filtered.sort(key=lambda c: c.created_at, reverse=True)
    chunk, next_cursor = paginate(filtered, limit, cursor)
    summaries = [content_to_summary(service, c) for c in chunk]
    return {"items": summaries, "next_cursor": next_cursor}


async def list_queue(
    repository: ContentRepository,
    *,
    content_type: ContentType | None = None,  # noqa: A002
    status: str | None = None,
    moderation_status: str | None = None,
    ai_label: str | None = None,
    has_reports: bool | None = None,
    author_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> QueueResponse:
    raw = await repository.list_queue(
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
    items: list[Any] = []
    for item in raw.get("items", []):
        if isinstance(item, ContentSummary):
            items.append(item)
        elif isinstance(item, Mapping):
            items.append(ContentSummary.model_validate(dict(item)))
        else:
            items.append(ContentSummary.model_validate(dict(item)))
    return build_queue_response(items, next_cursor=raw.get("next_cursor"))


async def get_content(
    service: PlatformModerationService,
    content_id: str,
    *,
    repository: ContentRepository | None = None,
) -> ContentSummary:
    async with service._lock:
        content = service._content.get(content_id)
        if not content:
            raise KeyError(content_id)
        summary = content_to_summary(service, content)

    if repository is None:
        return summary

    db_info = await repository.load_content_details(content_id)
    return merge_summary_with_db(summary, db_info)
