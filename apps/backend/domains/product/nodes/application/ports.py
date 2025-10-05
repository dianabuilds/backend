from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class NodeDTO:
    id: int
    slug: str
    author_id: str
    title: str | None
    tags: list[str]
    is_public: bool
    status: str | None = None
    publish_at: str | None = None
    unpublish_at: str | None = None
    content_html: str | None = None
    cover_url: str | None = None
    embedding: list[float] | None = None
    views_count: int = 0
    reactions_like_count: int = 0
    comments_disabled: bool = False
    comments_locked_by: str | None = None
    comments_locked_at: str | None = None


@dataclass(frozen=True)
class NodeViewStat:
    node_id: int
    bucket_date: str
    views: int


@dataclass(frozen=True)
class NodeReactionDTO:
    id: int
    node_id: int
    user_id: str
    reaction_type: str
    created_at: str


@dataclass(frozen=True)
class NodeReactionsSummary:
    node_id: int
    totals: dict[str, int]
    user_reaction: str | None = None


@dataclass(frozen=True)
class NodeCommentDTO:
    id: int
    node_id: int
    author_id: str
    parent_comment_id: int | None
    depth: int
    content: str
    status: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NodeCommentBanDTO:
    node_id: int
    target_user_id: str
    set_by: str
    reason: str | None
    created_at: str


@runtime_checkable
class Repo(Protocol):
    def get(self, node_id: int) -> NodeDTO | None: ...
    def get_by_slug(self, slug: str) -> NodeDTO | None: ...
    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO: ...
    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]: ...

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        is_public: bool,
        tags: Sequence[str] | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO: ...

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
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO: ...

    async def delete(self, node_id: int) -> bool: ...


@runtime_checkable
class NodeViewsRepo(Protocol):
    async def increment(
        self,
        node_id: int,
        *,
        amount: int = 1,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        at: str | None = None,
    ) -> int: ...

    async def get_total(self, node_id: int) -> int: ...

    async def get_daily(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]: ...


@runtime_checkable
class NodeViewsLimiter(Protocol):
    async def should_count(
        self,
        node_id: int,
        *,
        viewer_id: str | None,
        fingerprint: str | None,
        at: datetime,
    ) -> bool: ...


@runtime_checkable
class NodeReactionsRepo(Protocol):
    async def add(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool: ...

    async def remove(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool: ...

    async def has(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool: ...

    async def counts(self, node_id: int) -> dict[str, int]: ...

    async def list_for_node(
        self, node_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[NodeReactionDTO]: ...


@runtime_checkable
class NodeCommentsRepo(Protocol):
    async def create(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeCommentDTO: ...

    async def get(self, comment_id: int) -> NodeCommentDTO | None: ...

    async def list_for_node(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]: ...

    async def update_status(
        self,
        comment_id: int,
        status: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO: ...

    async def soft_delete(
        self,
        comment_id: int,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> bool: ...

    async def hard_delete(self, comment_id: int) -> bool: ...

    async def lock_node(
        self,
        node_id: int,
        *,
        locked_by: str | None,
        locked_at: str | None,
        reason: str | None = None,
    ) -> None: ...

    async def set_comments_disabled(
        self,
        node_id: int,
        *,
        disabled: bool,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...

    async def record_ban(
        self,
        node_id: int,
        target_user_id: str,
        *,
        set_by: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO: ...

    async def remove_ban(self, node_id: int, target_user_id: str) -> bool: ...

    async def is_banned(self, node_id: int, target_user_id: str) -> bool: ...

    async def list_bans(self, node_id: int) -> list[NodeCommentBanDTO]: ...


@runtime_checkable
class TagCatalog(Protocol):
    def ensure_canonical_slugs(self, slugs: Sequence[str]) -> list[str]: ...


@runtime_checkable
class Outbox(Protocol):
    def publish(self, topic: str, payload: dict, key: str | None = None) -> None: ...


@runtime_checkable
class UsageProjection(Protocol):
    def apply_diff(
        self, author_id: str, added: Sequence[str], removed: Sequence[str]
    ) -> None: ...
