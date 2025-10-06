from __future__ import annotations

from typing import TYPE_CHECKING

from ...domain.records import SanctionRecord, UserRecord

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService

__all__ = ["get_sanctions_for_user"]


def get_sanctions_for_user(
    service: PlatformModerationService, user: UserRecord
) -> list[SanctionRecord]:
    return sorted(
        [
            service._sanctions[sid]
            for sid in user.sanction_ids
            if sid in service._sanctions
        ],
        key=lambda s: s.issued_at,
        reverse=True,
    )
