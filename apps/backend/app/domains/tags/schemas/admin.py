from __future__ import annotations

from app.schemas.tag import (  # noqa: F401
    TagCreate,
)
from app.schemas.tags_admin import (  # noqa: F401
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
