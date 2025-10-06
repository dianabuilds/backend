from __future__ import annotations

from domains.product.tags.application.ports import Repo
from domains.product.tags.domain.results import TagView

from .store import TagUsageStore


class MemoryTagsRepo(Repo):
    def __init__(self, store: TagUsageStore) -> None:
        self._store = store
        # simple slug->name map
        self._names: dict[str, str] = {}

    @property
    def store(self) -> TagUsageStore:  # exposed for admin repo wiring
        return self._store

    def set_name(self, slug: str, name: str) -> None:
        self._names[str(slug)] = str(name)

    def list_for_user(
        self,
        user_id: str,
        q: str | None,
        popular: bool,
        limit: int,
        offset: int,
        content_type: str | None = None,
    ) -> list[TagView]:
        rows = self._store.list_for_user(
            user_id, q, popular, limit, offset, content_type
        )
        out: list[TagView] = []
        for slug, count in rows:
            out.append(
                TagView(
                    slug=str(slug),
                    name=self._names.get(str(slug), str(slug)),
                    count=int(count),
                )
            )
        return out
