from __future__ import annotations

from pydantic import BaseModel, Field


class TagOut(BaseModel):
    slug: str
    name: str
    count: int = 0


class NodeTagsUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list)


class AdminTagOut(BaseModel):
    slug: str
    name: str
    is_hidden: bool
    uses_count: int = 0


class TagCreate(BaseModel):
    slug: str
    name: str


class TagUpdate(BaseModel):
    name: str | None = None
    hidden: bool | None = None


class TagMerge(BaseModel):
    from_slug: str
    to_slug: str


class TagDetachRequest(BaseModel):
    node_ids: list[int] | None = None

__all__ = [
    "TagOut",
    "NodeTagsUpdate",
    "AdminTagOut",
    "TagCreate",
    "TagUpdate",
    "TagMerge",
    "TagDetachRequest",
]

