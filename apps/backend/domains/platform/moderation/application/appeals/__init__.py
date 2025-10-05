from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ...domain.dtos import AppealDTO
from .exceptions import ModerationAppealError
from .presenter import merge_appeal_with_db
from .repository import AppealsRepository, create_repository

if TYPE_CHECKING:
    from ..service import PlatformModerationService

__all__ = [
    "AppealsRepository",
    "UseCaseResult",
    "create_repository",
    "decide_appeal",
    "get_appeal",
    "list_appeals",
]


def __getattr__(name: str):  # pragma: no cover - compatibility export
    if name == "UseCaseResult":
        from .use_cases import UseCaseResult as _UseCaseResult

        globals()["UseCaseResult"] = _UseCaseResult
        return _UseCaseResult
    raise AttributeError(name)


def _use_cases():
    from . import use_cases

    return use_cases


def _resolve_repository(repository: AppealsRepository | None) -> AppealsRepository:
    return repository if repository is not None else AppealsRepository(None)


def _wrap_appeal_item(data: Mapping[str, Any]) -> Mapping[str, Any]:
    db_state = data.get("db_state") if isinstance(data, Mapping) else None
    return merge_appeal_with_db(data, db_state)


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
    repo = _resolve_repository(repository)
    use_cases = _use_cases()
    result = await use_cases.list_appeals(
        service,
        repo,
        status=status,
        user_id=user_id,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
    )
    payload = dict(result.payload)
    items = payload.get("items", [])
    payload["items"] = [_wrap_appeal_item(item) for item in items]
    return payload


async def get_appeal(
    service: PlatformModerationService,
    appeal_id: str,
    *,
    repository: AppealsRepository | None = None,
):
    has_repository = repository is not None
    repo = _resolve_repository(repository)
    use_cases = _use_cases()
    try:
        result = await use_cases.get_appeal(
            service,
            repo,
            appeal_id,
        )
    except ModerationAppealError as exc:
        raise KeyError(appeal_id) from exc
    payload = result.payload
    if has_repository:
        return _wrap_appeal_item(payload)
    return AppealDTO.model_validate(payload)


async def decide_appeal(
    service: PlatformModerationService,
    appeal_id: str,
    body: Mapping[str, Any],
    *,
    actor_id: str | None = None,
    repository: AppealsRepository | None = None,
) -> dict[str, Any]:
    repo = _resolve_repository(repository)
    use_cases = _use_cases()
    try:
        result = await use_cases.decide_appeal(
            service,
            repo,
            appeal_id=appeal_id,
            payload=dict(body),
            actor_id=actor_id,
        )
    except ModerationAppealError as exc:
        raise KeyError(appeal_id) from exc
    return result.payload
