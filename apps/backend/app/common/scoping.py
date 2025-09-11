from __future__ import annotations

from typing import Any

from sqlalchemy import Select


def apply_scope(
    query: Select,
    user: Any,
    scope_mode: str | None,
    account_id: int | None,  # kept for signature compatibility; ignored
) -> tuple[Select, int | None]:
    """Apply profile-centric scoping to a SQLAlchemy query.

    Profile-centric scoping. Supported modes:
    - mine: filter by current user's authored content
    - global: no author filter; visibility is handled by caller
    Other modes are accepted for compatibility but behave like "mine".
    """

    mode = (scope_mode or "mine").lower()

    if mode == "global":
        return query, None

    # Default: personal scope
    entity = query.column_descriptions[0]["entity"]
    if hasattr(entity, "author_id"):
        query = query.where(entity.author_id == getattr(user, "id", None))
    return query, None
