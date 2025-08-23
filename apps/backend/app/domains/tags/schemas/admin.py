from __future__ import annotations

from app.schemas.tags_admin import (  # noqa: F401
    TagListItem,
    AliasOut,
    MergeIn,
    MergeReport,
    BlacklistItem,
    BlacklistAdd,
)
from app.schemas.tag import (  # noqa: F401
    TagCreate,
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
