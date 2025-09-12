from __future__ import annotations

from app.domains.tags.schemas.tag import TagCreate  # noqa: F401
from app.domains.tags.schemas.tags_admin import (  # noqa: F401
    AliasOut,
    BlacklistAdd,
    BlacklistItem,
    MergeIn,
    MergeReport,
    TagListItem,
)

__all__ = [
    "TagListItem",
    "AliasOut",
    "MergeIn",
    "MergeReport",
    "BlacklistItem",
    "BlacklistAdd",
    "TagCreate",
]
