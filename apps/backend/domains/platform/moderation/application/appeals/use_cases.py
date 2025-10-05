from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..appeals import commands as appeal_commands
from ..appeals import queries as appeal_queries
from .exceptions import ModerationAppealError
from .repository import AppealsRepository

if TYPE_CHECKING:  # pragma: no cover
    from ..service import PlatformModerationService


@dataclass(slots=True)
class UseCaseResult:
    payload: dict[str, Any]
    status_code: int = 200


async def list_appeals(
    service: PlatformModerationService,
    repository: AppealsRepository,
    *,
    status: str | None = None,
    user_id: str | None = None,
    target_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> UseCaseResult:
    data = await appeal_queries.list_appeals(
        service,
        status=status,
        user_id=user_id,
        target_type=target_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        cursor=cursor,
        repository=repository,
    )
    return UseCaseResult(payload=data)


async def get_appeal(
    service: PlatformModerationService,
    repository: AppealsRepository,
    appeal_id: str,
) -> UseCaseResult:
    try:
        dto = await appeal_queries.get_appeal(
            service,
            appeal_id,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationAppealError(code="appeal_not_found", status_code=404) from exc
    payload = dto.model_dump() if hasattr(dto, "model_dump") else dict(dto)
    return UseCaseResult(payload=payload)


async def decide_appeal(
    service: PlatformModerationService,
    repository: AppealsRepository,
    *,
    appeal_id: str,
    payload: Mapping[str, Any],
    actor_id: str | None,
) -> UseCaseResult:
    try:
        decision = await appeal_commands.decide_appeal(
            service,
            appeal_id,
            dict(payload),
            actor_id=actor_id,
            repository=repository,
        )
    except KeyError as exc:
        raise ModerationAppealError(code="appeal_not_found", status_code=404) from exc
    return UseCaseResult(payload=decision)


__all__ = [
    "UseCaseResult",
    "decide_appeal",
    "get_appeal",
    "list_appeals",
]
