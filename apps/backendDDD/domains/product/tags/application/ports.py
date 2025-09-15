from __future__ import annotations

from typing import Protocol, runtime_checkable

from apps.backendDDD.domains.product.tags.domain.results import TagView


@runtime_checkable
class Repo(Protocol):
    def list_for_user(
        self,
        user_id: str,
        q: str | None,
        popular: bool,
        limit: int,
        offset: int,
        content_type: str | None = None,
    ) -> list[TagView]: ...
