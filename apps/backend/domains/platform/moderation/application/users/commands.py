from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from ...domain.records import UserRecord

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService


async def ensure_user_stub(
    service: PlatformModerationService,
    *,
    user_id: str,
    username: str,
    email: str | None = None,
) -> None:
    async with service._lock:
        if user_id in service._users:
            return
        service._users[user_id] = UserRecord(
            id=user_id,
            username=username or user_id,
            email=email,
            roles=["User"],
            status="active",
            registered_at=service._now(),
        )


async def update_roles(
    service: PlatformModerationService,
    user_id: str,
    add: Iterable[str],
    remove: Iterable[str],
) -> list[str]:
    async with service._lock:
        record = service._users.get(user_id)
        if not record:
            raise KeyError(user_id)
        current = {r for r in record.roles}
        for role in remove:
            if role is not None:
                current.discard(str(role))
        for role in add:
            if role is not None:
                current.add(str(role))
        record.roles = sorted(current, key=lambda r: r.lower())
        return list(record.roles)


__all__ = [
    "ensure_user_stub",
    "update_roles",
]
