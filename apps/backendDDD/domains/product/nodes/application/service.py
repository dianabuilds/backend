from __future__ import annotations

from collections.abc import Sequence

from apps.backendDDD.domains.product.nodes.application.ports import (
    Outbox,
    Repo,
    TagCatalog,
    UsageProjection,
)
from apps.backendDDD.domains.product.nodes.domain.results import NodeView
from apps.backendDDD.packages.core.telemetry import with_trace


class NodeService:
    def __init__(
        self,
        repo: Repo,
        tags: TagCatalog,
        outbox: Outbox,
        usage: UsageProjection | None = None,
    ):
        self.repo, self.tags, self.outbox, self.usage = repo, tags, outbox, usage

    def get(self, node_id: int) -> NodeView | None:
        n = self.repo.get(node_id)
        if not n:
            return None
        return NodeView(
            id=n.id,
            author_id=n.author_id,
            title=n.title,
            tags=list(n.tags),
            is_public=n.is_public,
        )

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeView]:
        items = self.repo.list_by_author(author_id, limit=limit, offset=offset)
        return [
            NodeView(
                id=i.id,
                author_id=i.author_id,
                title=i.title,
                tags=list(i.tags),
                is_public=i.is_public,
            )
            for i in items
        ]

    def update_tags(
        self, node_id: int, new_slugs: Sequence[str], *, actor_id: str
    ) -> NodeView:
        # Normalise & ensure tags exist
        slugs = self.tags.ensure_canonical_slugs(list(new_slugs))
        # Diff before/after for projection updates
        before = self.repo.get(node_id)
        updated = self.repo.set_tags(node_id, slugs)
        # Compute diff
        old = set(before.tags) if before is not None else set()
        new = set(slugs)
        added = sorted(new - old)
        removed = sorted(old - new)
        # Synchronous projection (optional)
        try:
            if before is not None and self.usage is not None and (added or removed):
                self.usage.apply_diff(before.author_id, added, removed)
        except Exception:
            # non-blocking
            pass
        # Publish event for projections (e.g. Tags usage counters, Search)
        try:
            self.outbox.publish(
                "node.tags.updated.v1",
                {
                    "id": updated.id,
                    "author_id": (
                        before.author_id if before is not None else updated.author_id
                    ),
                    "tags": list(slugs),
                    "added": added,
                    "removed": removed,
                    "content_type": "node",
                    "actor_id": actor_id,
                },
                key=f"node:{updated.id}:tags",
            )
        except Exception:
            # Do not block write on telemetry issues; monitoring will catch errors
            pass
        return NodeView(
            id=updated.id,
            author_id=updated.author_id,
            title=updated.title,
            tags=list(updated.tags),
            is_public=updated.is_public,
        )

    # --- New CRUD operations ---
    @with_trace
    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        tags: Sequence[str] | None,
        is_public: bool,
    ) -> NodeView:
        slugs = self.tags.ensure_canonical_slugs(list(tags or []))
        dto = await self.repo.create(
            author_id=author_id, title=title, is_public=bool(is_public), tags=slugs
        )
        try:
            self.outbox.publish(
                "node.created.v1",
                {
                    "id": dto.id,
                    "author_id": dto.author_id,
                    "title": dto.title,
                    "tags": list(dto.tags),
                    "is_public": dto.is_public,
                },
                key=f"node:{dto.id}",
            )
        except Exception:
            pass
        return NodeView(
            id=dto.id,
            author_id=dto.author_id,
            title=dto.title,
            tags=list(dto.tags),
            is_public=dto.is_public,
        )

    @with_trace
    async def update(
        self, node_id: int, *, title: str | None = None, is_public: bool | None = None
    ) -> NodeView:
        dto = await self.repo.update(node_id, title=title, is_public=is_public)
        changed = []
        if title is not None:
            changed.append("title")
        if is_public is not None:
            changed.append("is_public")
        try:
            if changed:
                self.outbox.publish(
                    "node.updated.v1",
                    {"id": dto.id, "fields": changed},
                    key=f"node:{dto.id}",
                )
        except Exception:
            pass
        return NodeView(
            id=dto.id,
            author_id=dto.author_id,
            title=dto.title,
            tags=list(dto.tags),
            is_public=dto.is_public,
        )

    @with_trace
    async def delete(self, node_id: int) -> bool:
        ok = await self.repo.delete(node_id)
        try:
            if ok:
                self.outbox.publish(
                    "node.deleted.v1", {"id": node_id}, key=f"node:{node_id}"
                )
        except Exception:
            pass
        return ok
