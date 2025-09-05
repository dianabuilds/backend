from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domains.tags.infrastructure.models.tag_models import TagAlias, TagBlacklist
from app.domains.tags.models import Tag


class ITagRepository(Protocol):
    # Listing
    async def list_with_counters(
        self, q: str | None, limit: int, offset: int
    ) -> list[dict[str, Any]]:  # pragma: no cover
        ...

    # Aliases
    async def list_aliases(self, tag_id: UUID) -> list[TagAlias]:  # pragma: no cover
        ...

    async def add_alias(self, tag_id: UUID, alias: str) -> TagAlias:  # pragma: no cover
        ...

    async def remove_alias(self, alias_id: UUID) -> None:  # pragma: no cover
        ...

    # Blacklist
    async def blacklist_list(self, q: str | None) -> list[TagBlacklist]:  # pragma: no cover
        ...

    async def blacklist_add(
        self, slug: str, reason: str | None
    ) -> TagBlacklist:  # pragma: no cover
        ...

    async def blacklist_delete(self, slug: str) -> None:  # pragma: no cover
        ...

    # CRUD
    async def create_tag(self, slug: str, name: str) -> Tag:  # pragma: no cover
        ...

    async def delete_tag(self, tag_id: UUID) -> None:  # pragma: no cover
        ...

    # Merge
    async def merge_dry_run(self, from_id: UUID, to_id: UUID) -> dict[str, Any]:  # pragma: no cover
        ...

    async def merge_apply(
        self, from_id: UUID, to_id: UUID, actor_id: str | None, reason: str | None
    ) -> dict[str, Any]:  # pragma: no cover
        ...

    # Optional compatibility for other parts of the app
    async def get_by_slug(self, slug: str) -> Tag | None:  # pragma: no cover
        ...

    async def create(self, slug: str, name: str) -> Tag:  # pragma: no cover
        ...
