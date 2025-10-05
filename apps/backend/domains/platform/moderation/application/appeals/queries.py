from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ...domain.dtos import AppealDTO
from ...domain.records import AppealRecord
from ..common import paginate, parse_iso_datetime, resolve_iso
from ..presenters.dto_builders import appeal_to_dto
from .presenter import build_list_response, merge_appeal_with_db
from .repository import AppealsRepository

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService


def _dto_to_mapping(dto: Any) -> dict[str, Any]:
    if hasattr(dto, "model_dump"):
        return dto.model_dump()  # type: ignore[no-any-return]
    if isinstance(dto, dict):
        return dict(dto)
    raise TypeError(f"Unsupported DTO type: {type(dto)!r}")


async def list_appeals(
    service: PlatformModerationService,
    *,
    status: str | None = None,
    user_id: str | None = None,
    target_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    repository: AppealsRepository | None = None,
) -> dict[str, Any]:
    async with service._lock:
        appeals = list(service._appeals.values())
        now = service._now()

    status_filter = status.lower() if status else None
    user_filter = user_id
    target_filter = target_type.lower() if target_type else None
    created_from = parse_iso_datetime(date_from)
    created_to = parse_iso_datetime(date_to)

    filtered: list[AppealRecord] = []
    for appeal in appeals:
        if status_filter and appeal.status.lower() != status_filter:
            continue
        if user_filter and appeal.user_id != user_filter:
            continue
        if target_filter and appeal.target_type.lower() != target_filter:
            continue
        created_at = appeal.created_at or now
        if created_from and created_at < created_from:
            continue
        if created_to and created_at > created_to:
            continue
        filtered.append(appeal)

    filtered.sort(
        key=lambda a: a.created_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    chunk, next_cursor = paginate(filtered, limit, cursor)
    iso = resolve_iso(service)
    dtos = [appeal_to_dto(a, iso=iso) for a in chunk]
    data_items = [_dto_to_mapping(dto) for dto in dtos]

    if repository is not None and data_items:
        db_map = await repository.fetch_many(item["id"] for item in data_items)
        data_items = [
            merge_appeal_with_db(item, db_map.get(item["id"])) for item in data_items
        ]

    return build_list_response(data_items, next_cursor=next_cursor)


async def get_appeal(
    service: PlatformModerationService,
    appeal_id: str,
    *,
    repository: AppealsRepository | None = None,
) -> AppealDTO | dict[str, Any]:
    async with service._lock:
        appeal = service._appeals.get(appeal_id)
        if not appeal:
            raise KeyError(appeal_id)
        iso = resolve_iso(service)
        dto = appeal_to_dto(appeal, iso=iso)

    if repository is None:
        return dto

    db_info = await repository.fetch_appeal(appeal_id)
    return merge_appeal_with_db(_dto_to_mapping(dto), db_info)


__all__ = ["get_appeal", "list_appeals"]
