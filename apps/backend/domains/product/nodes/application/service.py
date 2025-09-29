from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol, cast, runtime_checkable

try:
    from prometheus_client import Counter, Histogram  # type: ignore
except Exception:  # pragma: no cover
    Counter = Histogram = None  # type: ignore

from domains.product.nodes.application.embedding import EmbeddingClient
from domains.product.nodes.application.ports import (
    NodeDTO,
    Outbox,
    Repo,
    TagCatalog,
    UsageProjection,
)
from domains.product.nodes.domain.results import NodeView
from packages.core import with_trace


@runtime_checkable
class _EmbeddingRepo(Protocol):
    async def search_by_embedding(
        self, embedding: Sequence[float], *, limit: int = 64
    ) -> list[NodeDTO]: ...


logger = logging.getLogger(__name__)

if Counter is not None:
    EMBEDDING_REQUESTS = Counter(
        "node_embedding_requests_total",
        "Node embedding generation attempts",
        labelnames=("status", "provider"),
    )
else:
    EMBEDDING_REQUESTS = None

if Histogram is not None:
    EMBEDDING_LATENCY = Histogram(
        "node_embedding_latency_ms",
        "Latency of embedding generation in milliseconds",
        labelnames=("provider",),
        buckets=(10, 25, 50, 100, 200, 300, 500, 750, 1000, 1500, 2500),
    )
else:
    EMBEDDING_LATENCY = None


class NodeService:
    def __init__(
        self,
        repo: Repo,
        tags: TagCatalog,
        outbox: Outbox,
        usage: UsageProjection | None = None,
        embedding: EmbeddingClient | None = None,
    ) -> None:
        self.repo = repo
        self.tags = tags
        self.outbox = outbox
        self.usage = usage
        self.embedding = embedding

    def _record_embedding_metric(
        self,
        *,
        status: str,
        provider: str | None,
        duration_ms: float | None = None,
    ) -> None:
        if EMBEDDING_REQUESTS is not None:
            try:
                EMBEDDING_REQUESTS.labels(status=status, provider=provider or "unknown").inc()
            except Exception:
                pass
        if duration_ms is not None and EMBEDDING_LATENCY is not None and status == "success":
            try:
                EMBEDDING_LATENCY.labels(provider=provider or "unknown").observe(duration_ms)
            except Exception:
                pass

    async def _repo_get_async(self, node_id: int) -> NodeDTO | None:
        getter = getattr(self.repo, "_araw_get", None)
        if callable(getter):
            result = getter(node_id)
            if asyncio.iscoroutine(result):
                return await result
            return result
        maybe = self.repo.get(node_id)
        if asyncio.iscoroutine(maybe):
            return await maybe
        return maybe

    async def _repo_get_by_slug_async(self, slug: str) -> NodeDTO | None:
        getter = getattr(self.repo, "_araw_get_by_slug", None)
        if callable(getter):
            result = getter(slug)
            if asyncio.iscoroutine(result):
                return await result
            return result
        maybe = self.repo.get_by_slug(slug)
        if asyncio.iscoroutine(maybe):
            return await maybe
        return maybe

    async def _repo_set_tags_async(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        setter = getattr(self.repo, "_aset_tags", None)
        if callable(setter):
            result = setter(node_id, tags)
            if asyncio.iscoroutine(result):
                return await result
            return result
        result = self.repo.set_tags(node_id, tags)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _queue_embedding_job(self, node_id: int, *, reason: str) -> None:
        """Publish embedding recompute event if embedding is enabled."""
        if self.embedding is None or not self.embedding.enabled:
            return
        payload = {
            "id": int(node_id),
            "reason": reason,
            "requested_at": datetime.now(UTC).isoformat(),
        }
        try:
            self.outbox.publish("node.embedding.requested.v1", payload, key=f"node:{node_id}")
        except Exception:
            logger.warning("embedding_enqueue_failed", extra={"node_id": node_id, "reason": reason})

    def _to_view(self, dto: NodeDTO) -> NodeView:
        return NodeView(
            id=dto.id,
            slug=dto.slug,
            author_id=dto.author_id,
            title=dto.title,
            tags=list(dto.tags),
            is_public=dto.is_public,
            status=dto.status,
            publish_at=dto.publish_at,
            unpublish_at=dto.unpublish_at,
            content_html=dto.content_html,
            cover_url=dto.cover_url,
            embedding=list(dto.embedding) if dto.embedding is not None else None,
        )

    def _prepare_embedding_text(
        self,
        *,
        title: str | None,
        tags: Sequence[str] | None,
        content_html: str | None,
    ) -> str:
        parts: list[str] = []
        if title:
            parts.append(title.strip())
        if tags:
            tags_line = " ".join(t.strip() for t in tags if t)
            if tags_line:
                parts.append(tags_line)
        if content_html:
            stripped = re.sub(r"<[^>]+>", " ", content_html)
            stripped = stripped.strip()
            if stripped:
                parts.append(stripped)
        return "\n".join(part for part in parts if part).strip()

    async def _compute_embedding_vector(
        self,
        *,
        title: str | None,
        tags: Sequence[str] | None,
        content_html: str | None,
    ) -> list[float] | None:
        provider = getattr(self.embedding, "provider", None) if self.embedding is not None else None
        if self.embedding is None or not self.embedding.enabled:
            self._record_embedding_metric(status="disabled", provider=provider)
            return None
        text_value = self._prepare_embedding_text(
            title=title,
            tags=tags,
            content_html=content_html,
        )
        if not text_value:
            self._record_embedding_metric(status="no_input", provider=provider)
            return None
        start = time.perf_counter()
        try:
            vector = await self.embedding.embed(text_value)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("embedding_generation_failed", exc_info=exc)
            duration_ms = (time.perf_counter() - start) * 1000.0
            self._record_embedding_metric(
                status="error", provider=provider, duration_ms=duration_ms
            )
            return None
        duration_ms = (time.perf_counter() - start) * 1000.0
        if not vector:
            self._record_embedding_metric(
                status="empty", provider=provider, duration_ms=duration_ms
            )
            return None
        self._record_embedding_metric(status="success", provider=provider, duration_ms=duration_ms)
        return [float(v) for v in vector]

    def get(self, node_id: int) -> NodeView | None:
        dto = self.repo.get(node_id)
        if dto is None:
            return None
        return self._to_view(dto)

    def get_by_slug(self, slug: str) -> NodeView | None:
        dto = self.repo.get_by_slug(slug)
        if dto is None:
            return None
        return self._to_view(dto)

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0) -> list[NodeView]:
        items = self.repo.list_by_author(author_id, limit=limit, offset=offset)
        return [self._to_view(item) for item in items]

    def search_by_embedding(self, embedding: Sequence[float], *, limit: int = 64) -> list[NodeView]:
        if not isinstance(self.repo, _EmbeddingRepo):
            return []
        repo = cast(_EmbeddingRepo, self.repo)

        async def _run() -> list[NodeDTO]:
            return await repo.search_by_embedding(embedding, limit=limit)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            dtos = asyncio.run(_run())
        else:
            dtos = loop.run_until_complete(_run())  # type: ignore[misc]
        return [self._to_view(dto) for dto in dtos]

    async def update_tags(
        self, node_id: int, new_slugs: Sequence[str], *, actor_id: str
    ) -> NodeView:
        slugs = self.tags.ensure_canonical_slugs(list(new_slugs))
        before = await self._repo_get_async(node_id)
        updated = await self._repo_set_tags_async(node_id, slugs)
        old = set(before.tags) if before is not None else set()
        new = set(slugs)
        added = sorted(new - old)
        removed = sorted(old - new)
        try:
            if before is not None and self.usage is not None and (added or removed):
                self.usage.apply_diff(before.author_id, added, removed)
        except Exception:
            pass
        try:
            self.outbox.publish(
                "node.tags.updated.v1",
                {
                    "id": updated.id,
                    "author_id": (before.author_id if before is not None else updated.author_id),
                    "tags": list(slugs),
                    "added": added,
                    "removed": removed,
                    "content_type": "node",
                    "actor_id": actor_id,
                },
                key=f"node:{updated.id}:tags",
            )
        except Exception:
            pass
        self._queue_embedding_job(updated.id, reason="tags")
        return self._to_view(updated)

    @with_trace
    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        tags: Sequence[str] | None,
        is_public: bool,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
    ) -> NodeView:
        slugs = self.tags.ensure_canonical_slugs(list(tags or []))
        dto = await self.repo.create(
            author_id=author_id,
            title=title,
            is_public=bool(is_public),
            tags=slugs,
            status=status,
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            content_html=content_html,
            cover_url=cover_url,
            embedding=None,
        )
        if dto is None:
            logger.error(
                "node_create_failed",
                extra={
                    "author_id": author_id,
                    "title": title,
                    "tags": slugs,
                    "at": datetime.now(UTC).isoformat(),
                },
            )
            raise RuntimeError("node_create_failed")
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
        if slugs:
            try:
                self.outbox.publish(
                    "node.tags.updated.v1",
                    {
                        "id": dto.id,
                        "author_id": dto.author_id,
                        "content_type": "node",
                        "tags": list(slugs),
                        "added": list(slugs),
                        "removed": [],
                        "actor_id": author_id,
                    },
                    key=f"node:{dto.id}:tags",
                )
            except Exception:
                pass
        self._queue_embedding_job(dto.id, reason="create")
        return self._to_view(dto)

    @with_trace
    async def update(
        self,
        node_id: int,
        *,
        title: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
    ) -> NodeView:
        dto = await self.repo.update(
            node_id,
            title=title,
            is_public=is_public,
            status=status,
            publish_at=publish_at,
            unpublish_at=unpublish_at,
            content_html=content_html,
            cover_url=cover_url,
        )
        changed: list[str] = []
        if title is not None:
            changed.append("title")
        if is_public is not None:
            changed.append("is_public")
        if status is not None:
            changed.append("status")
        if publish_at is not None:
            changed.append("publish_at")
        if unpublish_at is not None:
            changed.append("unpublish_at")
        if content_html is not None:
            changed.append("content_html")
        if cover_url is not None:
            changed.append("cover_url")
        try:
            if changed:
                self.outbox.publish(
                    "node.updated.v1",
                    {"id": dto.id, "fields": changed},
                    key=f"node:{dto.id}",
                )
        except Exception:
            pass
        need_embedding = any(field in changed for field in {"title", "content_html"})
        if need_embedding:
            reason = "update"
            if changed:
                reason = f"update:{','.join(sorted(changed))}"
            self._queue_embedding_job(dto.id, reason=reason)
        return self._to_view(dto)

    @with_trace
    async def recompute_embedding(
        self, node_id: int, *, reason: str | None = None, force: bool = False
    ) -> NodeView | None:
        dto = await self._repo_get_async(node_id)
        if dto is None:
            return None
        if reason:
            try:
                logger.debug(
                    "embedding_recompute_requested", extra={"node_id": node_id, "reason": reason}
                )
            except Exception:
                pass
        if self.embedding is None or not self.embedding.enabled:
            return self._to_view(dto)
        vector = await self._compute_embedding_vector(
            title=dto.title,
            tags=dto.tags,
            content_html=dto.content_html,
        )
        if vector is None:
            if force:
                dto = await self.repo.update(node_id, embedding=None)
                return self._to_view(dto)
            return self._to_view(dto)
        dto = await self.repo.update(node_id, embedding=vector)
        if reason:
            try:
                logger.debug(
                    "embedding_recompute_done", extra={"node_id": node_id, "reason": reason}
                )
            except Exception:
                pass
        return self._to_view(dto)

    @with_trace
    async def delete(self, node_id: int) -> bool:
        ok = await self.repo.delete(node_id)
        try:
            if ok:
                self.outbox.publish("node.deleted.v1", {"id": node_id}, key=f"node:{node_id}")
        except Exception:
            pass
        return ok
