from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import Select


def apply_scope(
    query: Select,
    user: Any,
    scope_mode: str | None,
    account_id: int | None,
) -> tuple[Select, int | None]:
    """Apply scope filtering to a SQLAlchemy query.

    Parameters
    ----------
    query: ``Select``
        Base SQLAlchemy select query to modify.
    user: ``Any``
        Current authenticated user. ``user.id`` and ``user.role`` are used.
    scope_mode: ``str | None``
        Scope mode specifying how to filter the query. Supported values:
        ``mine``, ``member``, ``invited``, ``account:<id>``, ``global``.
    account_id: ``int | None``
        Account identifier from request path or context.

    Returns
    -------
    tuple
        Modified query and resolved account identifier (``None`` for global).
    """

    mode = scope_mode or "member"

    if mode == "global":
        if getattr(user, "role", None) != "admin":
            raise HTTPException(status_code=403, detail="Forbidden")
        return query, None

    if mode.startswith("account:"):
        try:
            resolved_account = int(mode.split(":", 1)[1])
        except ValueError as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=400, detail="Invalid scope_mode") from exc
    else:
        resolved_account = account_id
        if resolved_account is None:
            raise HTTPException(status_code=400, detail="account_id is required")

    entity = query.column_descriptions[0]["entity"]
    # Apply account filter
    if hasattr(entity, "account_id"):
        query = query.where(entity.account_id == resolved_account)

    # "mine" scope additionally filters by author
    if mode == "mine" and hasattr(entity, "author_id"):
        query = query.where(entity.author_id == user.id)

    return query, resolved_account
