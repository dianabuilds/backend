from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import UUID

from domains.product.content.domain import (
    HomeConfig,
    HomeConfigAudit,
    HomeConfigHistoryEntry,
)


class HomeConfigRepositoryPort(Protocol):
    async def get_by_id(self, config_id: UUID) -> HomeConfig | None: ...

    async def get_active(self, slug: str) -> HomeConfig | None: ...

    async def list_history(
        self,
        slug: str,
        *,
        limit: int = 20,
    ) -> list[HomeConfigHistoryEntry]: ...

    async def get_draft(self, slug: str) -> HomeConfig | None: ...

    async def create_draft(
        self,
        slug: str,
        data: Mapping[str, Any],
        *,
        actor: str | None,
        base_config_id: UUID | None,
    ) -> HomeConfig: ...

    async def update_draft(
        self,
        config_id: UUID,
        data: Mapping[str, Any],
        *,
        actor: str | None,
    ) -> HomeConfig: ...

    async def publish(
        self,
        config_id: UUID,
        *,
        actor: str | None,
    ) -> HomeConfig: ...

    async def restore_version(
        self,
        slug: str,
        version: int,
        *,
        actor: str | None,
    ) -> HomeConfig: ...

    async def add_audit(
        self,
        *,
        config_id: UUID,
        version: int,
        action: str,
        actor: str | None,
        actor_team: str | None,
        comment: str | None,
        data: Mapping[str, Any] | None,
        diff: list[dict[str, Any]] | None,
    ) -> HomeConfigAudit: ...


__all__ = ["HomeConfigRepositoryPort"]
