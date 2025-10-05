from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from ...domain.dtos import (
    SanctionStatus,
    SanctionType,
)
from ...domain.records import UserRecord
from ..common import paginate, parse_iso_datetime
from ..sanctions import get_sanctions_for_user
from .presenter import user_to_detail, user_to_summary

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService


async def warnings_count_recent(
    service: PlatformModerationService,
    user_id: str,
    *,
    days: int = 10,
) -> int:
    """Count active warnings for user_id issued within the last days."""
    async with service._lock:
        user = service._users.get(user_id)
        if not user:
            return 0
        since = service._now() - timedelta(days=int(days))
        cnt = 0
        for sid in user.sanction_ids:
            sanction = service._sanctions.get(sid)
            if (
                sanction
                and sanction.type == SanctionType.warning
                and sanction.status == SanctionStatus.active
                and sanction.issued_at >= since
            ):
                cnt += 1
        return cnt


async def list_users(
    service: PlatformModerationService,
    *,
    status: str | None = None,
    role: str | None = None,
    registered_from: str | None = None,
    registered_to: str | None = None,
    q: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    async with service._lock:
        users = list(service._users.values())

    status_filters = {
        ("banned" if s in {"ban", "banned"} else s.lower())
        for s in (status.split(",") if status else [])
        if s
    }
    role_filters = {r.lower() for r in (role.split(",") if role else []) if r}
    reg_from = parse_iso_datetime(registered_from)
    reg_to = parse_iso_datetime(registered_to)
    q_norm = q.lower().strip() if q else None

    filtered: list[UserRecord] = []
    for user in users:
        user_statuses = {user.status.lower()}
        for sanction in get_sanctions_for_user(service, user):
            if sanction.status == SanctionStatus.active:
                user_statuses.add(sanction.type.value.lower())
                if sanction.type == SanctionType.ban:
                    user_statuses.add("banned")
        if status_filters and not (user_statuses & status_filters):
            continue
        if role_filters and not any(r.lower() in role_filters for r in user.roles):
            continue
        if reg_from and user.registered_at < reg_from:
            continue
        if reg_to and user.registered_at > reg_to:
            continue
        if q_norm:
            haystack = " ".join(filter(None, [user.username, user.email])).lower()
            if q_norm not in haystack:
                continue
        filtered.append(user)

    filtered.sort(key=lambda u: u.registered_at, reverse=True)
    chunk, next_cursor = paginate(filtered, limit, cursor)
    return {
        "items": [user_to_summary(service, u) for u in chunk],
        "next_cursor": next_cursor,
    }


async def get_user(
    service: PlatformModerationService,
    user_id: str,
):
    async with service._lock:
        record = service._users.get(user_id)
        if not record:
            raise KeyError(user_id)
        return user_to_detail(service, record)


__all__ = [
    "warnings_count_recent",
    "list_users",
    "get_user",
]
