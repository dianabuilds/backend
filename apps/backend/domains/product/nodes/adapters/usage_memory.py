from __future__ import annotations

from collections.abc import Sequence

from domains.product.nodes.application.ports import UsageProjection
from domains.product.tags.adapters.store_memory import TagUsageStore


class MemoryUsageProjection(UsageProjection):
    def __init__(self, store: TagUsageStore, *, content_type: str = "node") -> None:
        self.store = store
        self.content_type = content_type

    def apply_diff(
        self, author_id: str, added: Sequence[str], removed: Sequence[str]
    ) -> None:
        self.store.apply_diff(author_id, added, removed, content_type=self.content_type)
