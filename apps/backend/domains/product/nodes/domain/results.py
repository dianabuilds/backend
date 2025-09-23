from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeView:
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
