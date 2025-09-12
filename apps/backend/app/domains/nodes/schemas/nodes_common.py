from __future__ import annotations

from enum import Enum


class NodeType(str, Enum):
    """Supported node types."""

    quest = "quest"


class Status(str, Enum):
    draft = "draft"
    in_review = "in_review"
    published = "published"
    archived = "archived"


class Visibility(str, Enum):
    private = "private"
    unlisted = "unlisted"
    public = "public"


# Simple type alias for node version numbers
Version = int

__all__ = ["NodeType", "Status", "Visibility", "Version"]

