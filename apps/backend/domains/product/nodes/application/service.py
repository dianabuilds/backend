from __future__ import annotations

import logging
import re
import time
from collections.abc import Awaitable, Sequence
from datetime import UTC, datetime
from inspect import isawaitable
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

try:
    from prometheus_client import Counter, Histogram  # type: ignore
except ImportError:  # pragma: no cover
    Counter = Histogram = None  # type: ignore

from domains.product.nodes.application.embedding import EmbeddingClient
from domains.product.nodes.application.engagement import (
    NodeCommentsService,
    NodeReactionsService,
    NodeViewsService,
)
from domains.product.nodes.application.interactors.events import (
    NodeEvent,
    NodeEventPublisher,
)
from domains.product.nodes.application.ports import (
    NodeCache,
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeDTO,
    NodeReactionsSummary,
    NodeViewStat,
    Outbox,
    Repo,
    TagCatalog,
    UsageProjection,
)
from domains.product.nodes.domain.results import NodeView
from packages.core import with_trace
from packages.core.async_utils import run_sync, submit_async


@runtime_checkable
class _EmbeddingRepo(Protocol):
    async def search_by_embedding(
        self, embedding: Sequence[float], *, limit: int = 64
    ) -> list[NodeDTO]: ...


logger = logging.getLogger(__name__)

TResult = TypeVar("TResult")


async def _await_maybe(value: TResult | Awaitable[TResult]) -> TResult:
    if isawaitable(value):
        return await cast(Awaitable[TResult], value)
    return cast(TResult, value)


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
        event_publisher: NodeEventPublisher | None = None,
        usage: UsageProjection | None = None,
        embedding: EmbeddingClient | None = None,
        views: NodeViewsService | None = None,
        reactions: NodeReactionsService | None = None,
        comments: NodeCommentsService | None = None,
        cache: NodeCache | None = None,
    ) -> None:
        self.repo = repo
        self.tags = tags
        self.outbox = outbox
        self._events = event_publisher or NodeEventPublisher(outbox)
        self.usage = usage
        self.embedding = embedding
        self.views_service = views
        self.reactions_service = reactions
        self.comments_service = comments
        self.cache = cache

    async def _cache_get_by_id(self, node_id: int) -> NodeDTO | None:
        if self.cache is None:
            return None
        try:
            return await self.cache.get(node_id)
        except Exception as exc:
            logger.debug(
                "node_cache_get_failed", extra={"node_id": node_id}, exc_info=exc
            )
            return None

    async def _cache_get_by_slug(self, slug: str) -> NodeDTO | None:
        if self.cache is None:
            return None
        try:
            return await self.cache.get_by_slug(slug)
        except Exception as exc:
            logger.debug(
                "node_cache_get_slug_failed", extra={"slug": slug}, exc_info=exc
            )
            return None

    async def _cache_store(self, dto: NodeDTO) -> None:
        if self.cache is None:
            return
        try:
            await self.cache.set(dto)
        except Exception as exc:
            logger.debug(
                "node_cache_store_failed", extra={"node_id": dto.id}, exc_info=exc
            )

    async def _cache_invalidate(self, node_id: int, slug: str | None = None) -> None:
        if self.cache is None:
            return
        try:
            await self.cache.invalidate(node_id, slug=slug)
        except Exception as exc:
            logger.debug(
                "node_cache_invalidate_failed", extra={"node_id": node_id}, exc_info=exc
            )

    async def _cache_store_many(self, dtos: Sequence[NodeDTO]) -> None:
        if self.cache is None:
            return
        for dto in dtos:
            await self._cache_store(dto)

    def _require_views_service(self) -> NodeViewsService:
        if self.views_service is None:
            raise RuntimeError("node_views_service_not_configured")
        return self.views_service

    def _require_reactions_service(self) -> NodeReactionsService:
        if self.reactions_service is None:
            raise RuntimeError("node_reactions_service_not_configured")
        return self.reactions_service

    def _require_comments_service(self) -> NodeCommentsService:
        if self.comments_service is None:
            raise RuntimeError("node_comments_service_not_configured")
        return self.comments_service

    def _safe_publish(
        self,
        event: str,
        payload: dict[str, Any],
        *,
        key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._events.publish(
            NodeEvent(
                name=event,
                payload=dict(payload),
                key=key,
                context=dict(context) if context else None,
            )
        )

    def _record_embedding_metric(
        self,
        *,
        status: str,
        provider: str | None,
        duration_ms: float | None = None,
    ) -> None:
        if EMBEDDING_REQUESTS is not None:
            try:
                EMBEDDING_REQUESTS.labels(
                    status=status, provider=provider or "unknown"
                ).inc()
            except Exception as exc:
                logger.debug("embedding_metric_emit_failed", exc_info=exc)
        if (
            duration_ms is not None
            and EMBEDDING_LATENCY is not None
            and status == "success"
        ):
            try:
                EMBEDDING_LATENCY.labels(provider=provider or "unknown").observe(
                    duration_ms
                )
            except Exception as exc:
                logger.debug("embedding_latency_emit_failed", exc_info=exc)

    async def _repo_get_async(self, node_id: int) -> NodeDTO | None:
        cached = await self._cache_get_by_id(node_id)
        if cached is not None:
            return cached
        getter = getattr(self.repo, "_araw_get", None)
        if callable(getter):
            result = getter(node_id)
            dto = await _await_maybe(
                cast(NodeDTO | None | Awaitable[NodeDTO | None], result)
            )
        else:
            result = self.repo.get(node_id)
            dto = await _await_maybe(
                cast(NodeDTO | None | Awaitable[NodeDTO | None], result)
            )
        if dto is not None:
            await self._cache_store(dto)
        return dto

    async def _repo_get_by_slug_async(self, slug: str) -> NodeDTO | None:
        cached = await self._cache_get_by_slug(slug)
        if cached is not None:
            return cached
        getter = getattr(self.repo, "_araw_get_by_slug", None)
        if callable(getter):
            result = getter(slug)
            dto = await _await_maybe(
                cast(NodeDTO | None | Awaitable[NodeDTO | None], result)
            )
        else:
            result = self.repo.get_by_slug(slug)
            dto = await _await_maybe(
                cast(NodeDTO | None | Awaitable[NodeDTO | None], result)
            )
        if dto is not None:
            await self._cache_store(dto)
        return dto

    async def _repo_set_tags_async(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        setter = getattr(self.repo, "_aset_tags", None)
        if callable(setter):
            result = setter(node_id, tags)
            dto = await _await_maybe(cast(NodeDTO | Awaitable[NodeDTO], result))
        else:
            result = self.repo.set_tags(node_id, tags)
            dto = await _await_maybe(cast(NodeDTO | Awaitable[NodeDTO], result))
        await self._cache_store(dto)
        return dto

    def _queue_embedding_job(self, node_id: int, *, reason: str) -> None:
        """Publish embedding recompute event if embedding is enabled."""
        if self.embedding is None or not self.embedding.enabled:
            return
        payload = {
            "id": int(node_id),
            "reason": reason,
            "requested_at": datetime.now(UTC).isoformat(),
        }
        self._safe_publish(
            "node.embedding.requested.v1",
            payload,
            key=f"node:{node_id}",
            context={"node_id": node_id, "reason": reason},
        )

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
            views_count=dto.views_count,
            reactions_like_count=dto.reactions_like_count,
            comments_disabled=dto.comments_disabled,
            comments_locked_by=dto.comments_locked_by,
            comments_locked_at=dto.comments_locked_at,
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
        provider = (
            getattr(self.embedding, "provider", None)
            if self.embedding is not None
            else None
        )
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
        self._record_embedding_metric(
            status="success", provider=provider, duration_ms=duration_ms
        )
        return [float(v) for v in vector]

    def get(self, node_id: int) -> NodeView | None:
        dto = run_sync(self._repo_get_async(node_id))
        if dto is None:
            return None
        return self._to_view(dto)

    def get_by_slug(self, slug: str) -> NodeView | None:
        dto = run_sync(self._repo_get_by_slug_async(slug))
        if dto is None:
            return None
        return self._to_view(dto)

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeView]:
        items = self.repo.list_by_author(author_id, limit=limit, offset=offset)
        if items:
            submit_async(self._cache_store_many(items))
        return [self._to_view(item) for item in items]

    def search_by_embedding(
        self, embedding: Sequence[float], *, limit: int = 64
    ) -> list[NodeView]:
        if not isinstance(self.repo, _EmbeddingRepo):
            return []
        repo = cast(_EmbeddingRepo, self.repo)

        async def _run() -> list[NodeDTO]:
            return await repo.search_by_embedding(embedding, limit=limit)

        dtos = run_sync(_run())
        if dtos:
            submit_async(self._cache_store_many(dtos))
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
        if before is not None and self.usage is not None and (added or removed):
            try:
                self.usage.apply_diff(before.author_id, added, removed)
            except Exception as exc:
                logger.warning(
                    "node_usage_diff_failed",
                    extra={"author_id": before.author_id, "node_id": node_id},
                    exc_info=exc,
                )
        self._safe_publish(
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
            context={"node_id": updated.id},
        )
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
        await self._cache_store(dto)
        self._safe_publish(
            "node.created.v1",
            {
                "id": dto.id,
                "author_id": dto.author_id,
                "title": dto.title,
                "tags": list(dto.tags),
                "is_public": dto.is_public,
            },
            key=f"node:{dto.id}",
            context={"node_id": dto.id},
        )
        if slugs:
            self._safe_publish(
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
                context={"node_id": dto.id, "author_id": dto.author_id},
            )
        self._queue_embedding_job(dto.id, reason="create")
        return self._to_view(dto)

    @with_trace
    async def register_view(
        self,
        node_id: int,
        *,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        amount: int = 1,
        at: datetime | None = None,
    ) -> int:
        service = self._require_views_service()
        base_ts = at or datetime.now(UTC)
        if base_ts.tzinfo is None:
            base_ts = base_ts.replace(tzinfo=UTC)
        when = base_ts.astimezone(UTC).replace(microsecond=0)
        total = await service.register_view(
            node_id,
            viewer_id=viewer_id,
            fingerprint=fingerprint,
            amount=amount,
            at=when,
        )
        self._safe_publish(
            "node.viewed.v1",
            {
                "id": node_id,
                "viewer_id": viewer_id,
                "fingerprint": fingerprint,
                "amount": amount,
                "total": total,
                "at": when.isoformat(),
            },
            key=f"node:{node_id}:views",
            context={"node_id": node_id},
        )
        return total

    async def get_total_views(self, node_id: int) -> int:
        service = self._require_views_service()
        return await service.get_total(node_id)

    async def get_view_stats(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]:
        service = self._require_views_service()
        return await service.get_daily(node_id, limit=limit, offset=offset)

    @with_trace
    async def add_like(self, node_id: int, *, user_id: str) -> bool:
        service = self._require_reactions_service()
        created = await service.add_like(node_id, user_id)
        if created:
            self._safe_publish(
                "node.reaction.added.v1",
                {"id": node_id, "user_id": user_id, "reaction_type": "like"},
                key=f"node:{node_id}:reaction:{user_id}",
                context={"node_id": node_id, "user_id": user_id},
            )
        return created

    @with_trace
    async def remove_like(self, node_id: int, *, user_id: str) -> bool:
        service = self._require_reactions_service()
        removed = await service.remove_like(node_id, user_id)
        if removed:
            self._safe_publish(
                "node.reaction.removed.v1",
                {"id": node_id, "user_id": user_id, "reaction_type": "like"},
                key=f"node:{node_id}:reaction:{user_id}",
                context={"node_id": node_id, "user_id": user_id},
            )
        return removed

    @with_trace
    async def toggle_like(self, node_id: int, *, user_id: str) -> bool:
        service = self._require_reactions_service()
        added = await service.toggle_like(node_id, user_id)
        event = "node.reaction.added.v1" if added else "node.reaction.removed.v1"
        self._safe_publish(
            event,
            {"id": node_id, "user_id": user_id, "reaction_type": "like"},
            key=f"node:{node_id}:reaction:{user_id}",
            context={"node_id": node_id, "user_id": user_id},
        )
        return added

    async def get_reactions_summary(
        self, node_id: int, *, user_id: str | None = None
    ) -> NodeReactionsSummary:
        service = self._require_reactions_service()
        return await service.get_summary(node_id, user_id=user_id)

    @with_trace
    async def create_comment(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeCommentDTO:
        service = self._require_comments_service()
        comment = await service.create_comment(
            node_id=node_id,
            author_id=author_id,
            content=content,
            parent_comment_id=parent_comment_id,
            metadata=metadata,
        )
        self._safe_publish(
            "node.comment.created.v1",
            {
                "id": comment.id,
                "node_id": comment.node_id,
                "author_id": comment.author_id,
                "parent_comment_id": comment.parent_comment_id,
                "status": comment.status,
            },
            key=f"node:{node_id}:comment:{comment.id}",
            context={"node_id": node_id, "comment_id": comment.id},
        )
        return comment

    async def get_comment(self, comment_id: int) -> NodeCommentDTO | None:
        service = self._require_comments_service()
        return await service.get_comment(comment_id)

    async def list_comments(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]:
        service = self._require_comments_service()
        return await service.list_comments(
            node_id,
            parent_comment_id=parent_comment_id,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )

    @with_trace
    async def delete_comment(
        self,
        comment_id: int,
        *,
        actor_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> bool:
        service = self._require_comments_service()
        comment = await service.get_comment(comment_id)
        if comment is None:
            return False
        removed = await service.delete_comment(
            comment_id, actor_id=actor_id, hard=hard, reason=reason
        )
        if removed:
            self._safe_publish(
                "node.comment.deleted.v1",
                {
                    "id": comment_id,
                    "node_id": comment.node_id,
                    "actor_id": actor_id,
                    "hard": hard,
                },
                key=f"node:{comment.node_id}:comment:{comment_id}",
                context={"node_id": comment.node_id, "comment_id": comment_id},
            )
        return removed

    @with_trace
    async def update_comment_status(
        self,
        comment_id: int,
        *,
        status: str,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO:
        service = self._require_comments_service()
        updated = await service.update_status(
            comment_id, status=status, actor_id=actor_id, reason=reason
        )
        self._safe_publish(
            "node.comment.status_changed.v1",
            {
                "id": updated.id,
                "node_id": updated.node_id,
                "status": updated.status,
                "actor_id": actor_id,
            },
            key=f"node:{updated.node_id}:comment:{updated.id}:status",
            context={"node_id": updated.node_id, "comment_id": updated.id},
        )
        return updated

    @with_trace
    async def lock_comments(
        self, node_id: int, *, actor_id: str, reason: str | None = None
    ) -> None:
        service = self._require_comments_service()
        await service.lock_comments(node_id, actor_id=actor_id, reason=reason)
        self._safe_publish(
            "node.comments.locked.v1",
            {"id": node_id, "actor_id": actor_id, "reason": reason},
            key=f"node:{node_id}:comments:lock",
            context={"node_id": node_id},
        )

    @with_trace
    async def unlock_comments(
        self, node_id: int, *, actor_id: str | None = None
    ) -> None:
        service = self._require_comments_service()
        await service.unlock_comments(node_id, actor_id=actor_id)
        self._safe_publish(
            "node.comments.unlocked.v1",
            {"id": node_id, "actor_id": actor_id},
            key=f"node:{node_id}:comments:lock",
            context={"node_id": node_id},
        )

    @with_trace
    async def disable_comments(
        self, node_id: int, *, actor_id: str | None = None, reason: str | None = None
    ) -> None:
        service = self._require_comments_service()
        await service.disable_comments(node_id, actor_id=actor_id, reason=reason)
        self._safe_publish(
            "node.comments.disabled.v1",
            {"id": node_id, "actor_id": actor_id, "reason": reason},
            key=f"node:{node_id}:comments:disable",
            context={"node_id": node_id},
        )

    @with_trace
    async def enable_comments(
        self, node_id: int, *, actor_id: str | None = None, reason: str | None = None
    ) -> None:
        service = self._require_comments_service()
        await service.enable_comments(node_id, actor_id=actor_id, reason=reason)
        self._safe_publish(
            "node.comments.enabled.v1",
            {"id": node_id, "actor_id": actor_id, "reason": reason},
            key=f"node:{node_id}:comments:disable",
            context={"node_id": node_id},
        )

    @with_trace
    async def ban_comment_user(
        self,
        node_id: int,
        target_user_id: str,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO:
        service = self._require_comments_service()
        ban = await service.ban_user(
            node_id, target_user_id=target_user_id, actor_id=actor_id, reason=reason
        )
        self._safe_publish(
            "node.comments.user_banned.v1",
            {
                "node_id": node_id,
                "target_user_id": target_user_id,
                "set_by": actor_id,
                "reason": reason,
            },
            key=f"node:{node_id}:comments:ban:{target_user_id}",
            context={"node_id": node_id, "target_user_id": target_user_id},
        )
        return ban

    @with_trace
    async def unban_comment_user(self, node_id: int, target_user_id: str) -> bool:
        service = self._require_comments_service()
        result = await service.unban_user(node_id, target_user_id)
        if result:
            self._safe_publish(
                "node.comments.user_unbanned.v1",
                {"node_id": node_id, "target_user_id": target_user_id},
                key=f"node:{node_id}:comments:ban:{target_user_id}",
                context={"node_id": node_id, "target_user_id": target_user_id},
            )
        return result

    async def is_comment_user_banned(self, node_id: int, target_user_id: str) -> bool:
        service = self._require_comments_service()
        return await service.is_user_banned(node_id, target_user_id)

    async def list_comment_bans(self, node_id: int) -> list[NodeCommentBanDTO]:
        service = self._require_comments_service()
        return await service.list_bans(node_id)

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
        await self._cache_store(dto)
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
        if changed:
            self._safe_publish(
                "node.updated.v1",
                {"id": dto.id, "fields": changed},
                key=f"node:{dto.id}",
                context={"node_id": dto.id},
            )
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
            logger.debug(
                "embedding_recompute_requested",
                extra={"node_id": node_id, "reason": reason},
            )
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
                await self._cache_store(dto)
                return self._to_view(dto)
            return self._to_view(dto)
        dto = await self.repo.update(node_id, embedding=vector)
        await self._cache_store(dto)
        if reason:
            logger.debug(
                "embedding_recompute_done", extra={"node_id": node_id, "reason": reason}
            )
        return self._to_view(dto)

    @with_trace
    async def delete(self, node_id: int) -> bool:
        ok = await self.repo.delete(node_id)
        if ok:
            await self._cache_invalidate(node_id)
            self._safe_publish(
                "node.deleted.v1",
                {"id": node_id},
                key=f"node:{node_id}",
                context={"node_id": node_id},
            )
        return ok
