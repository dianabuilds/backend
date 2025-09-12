from __future__ import annotations

import hashlib
from typing import Any, Mapping

from sqlalchemy import and_

MAX_JS_SAFE_INT = (1 << 53) - 1  # 9007199254740991


def _hash_to_int(value: str) -> int:
    h = hashlib.blake2b(value.encode("utf-8", errors="ignore"), digest_size=8).digest()
    num = int.from_bytes(h, byteorder="big", signed=False)
    return num & MAX_JS_SAFE_INT


def scope_id_from_any(obj: Any) -> int:
    if isinstance(obj, int):
        return abs(obj) & MAX_JS_SAFE_INT
    return _hash_to_int(str(obj))


def get_user_scope_id(user: Any) -> int:
    uid = getattr(user, "id", None)
    return scope_id_from_any(uid if uid is not None else user)


def get_node_scope_id(node: Any) -> int:
    aid = getattr(node, "author_id", None)
    return scope_id_from_any(aid if aid is not None else node)


def apply_scope(stmt, user: Any | None, mode: str) -> tuple[object, Mapping[str, Any]]:
    """Apply simple per-user scoping to a SQLAlchemy Select.

    - For modes like "own", "author", "profile" filters by ``author_id == user.id``
      when the entity has such a column.
    - Returns the possibly modified statement and a dict of applied values.
    """
    applied: dict[str, Any] = {}
    if user is None or not mode:
        return stmt, applied
    mode = str(mode).lower()
    if mode in {"own", "author", "profile"}:
        profile_id = getattr(user, "id", None) or getattr(user, "profile_id", None)
        if profile_id is None:
            return stmt, applied
        try:
            entity = stmt.column_descriptions[0]["entity"]  # type: ignore[index]
        except Exception:
            return stmt, applied
        if hasattr(entity, "author_id"):
            stmt = stmt.where(getattr(entity, "author_id") == profile_id)
            applied["profile_id"] = profile_id
    return stmt, applied


__all__ = [
    "MAX_JS_SAFE_INT",
    "scope_id_from_any",
    "get_user_scope_id",
    "get_node_scope_id",
    "apply_scope",
]

