from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol

from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastCollection,
    BroadcastCreateModel,
    BroadcastStatus,
    BroadcastUpdateModel,
)
from domains.platform.notifications.domain.template import Template
from domains.platform.notifications.models.entities import (
    ConsentAuditRecord,
    NotificationMatrix,
    PreferenceRecord,
)


class TemplateRepo(Protocol):
    async def upsert(self, payload: dict[str, Any]) -> Template: ...
    async def list(self, limit: int = 50, offset: int = 0) -> list[Template]: ...
    async def get(self, template_id: str) -> Template | None: ...
    async def get_by_slug(self, slug: str) -> Template | None: ...
    async def delete(self, template_id: str) -> None: ...


class BroadcastRepo(Protocol):
    async def create(self, payload: BroadcastCreateModel) -> Broadcast: ...

    async def update(self, broadcast_id: str, payload: BroadcastUpdateModel) -> Broadcast: ...

    async def update_status(
        self,
        broadcast_id: str,
        *,
        status: BroadcastStatus,
        scheduled_at: datetime | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        total: int | None = None,
        sent: int | None = None,
        failed: int | None = None,
    ) -> Broadcast: ...

    async def claim_due(self, now: datetime, limit: int = 10) -> list[Broadcast]: ...

    async def claim(self, broadcast_id: str, *, now: datetime) -> Broadcast | None: ...

    async def get(self, broadcast_id: str) -> Broadcast | None: ...

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        statuses: Sequence[BroadcastStatus] | None = None,
        query: str | None = None,
    ) -> BroadcastCollection: ...


class NotificationMatrixRepo(Protocol):
    async def load(self, *, use_cache: bool = True) -> NotificationMatrix: ...


class NotificationPreferenceRepo(Protocol):
    async def list_for_user(self, user_id: str) -> list[PreferenceRecord]: ...
    async def replace_for_user(self, user_id: str, records: Sequence[PreferenceRecord]) -> None: ...


class NotificationConsentAuditRepo(Protocol):
    async def append_many(self, records: Sequence[ConsentAuditRecord]) -> None: ...


__all__ = [
    "BroadcastRepo",
    "NotificationConsentAuditRepo",
    "NotificationMatrixRepo",
    "NotificationPreferenceRepo",
    "TemplateRepo",
]
