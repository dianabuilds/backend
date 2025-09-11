from __future__ import annotations

import hashlib
from typing import Any

MAX_JS_SAFE_INT = (1 << 53) - 1  # 9007199254740991


def _hash_to_int(value: str) -> int:
    """Return a stable positive 53-bit integer for an arbitrary string.

    We avoid UUIDs altogether: inputs are coerced to string and hashed with
    BLAKE2b (8-byte digest), then truncated to a JS-safe integer range. This
    yields a deterministic small integer suitable for logging/metrics keys and
    cache partitioning.
    """

    h = hashlib.blake2b(value.encode("utf-8", errors="ignore"), digest_size=8).digest()
    num = int.from_bytes(h, byteorder="big", signed=False)
    return num & MAX_JS_SAFE_INT


def scope_id_from_any(obj: Any) -> int:
    """Compute a numeric scope id from various inputs.

    - If ``obj`` is an int, return its absolute value (bounded to JS safe).
    - Otherwise, convert to string and hash deterministically to a 53-bit int.
    """

    if isinstance(obj, int):
        return abs(obj) & MAX_JS_SAFE_INT
    return _hash_to_int(str(obj))


def get_user_scope_id(user: Any) -> int:
    """Return a numeric scope id for a user-like object.

    Expects ``user`` to have an ``id`` attribute. Falls back to hashing the
    whole object if not present.
    """

    uid = getattr(user, "id", None)
    return scope_id_from_any(uid if uid is not None else user)


def get_node_scope_id(node: Any) -> int:
    """Return a numeric scope id for a node-like object.

    Uses ``node.author_id`` when available; otherwise falls back to hashing
    the node itself.
    """

    aid = getattr(node, "author_id", None)
    return scope_id_from_any(aid if aid is not None else node)


__all__ = [
    "MAX_JS_SAFE_INT",
    "scope_id_from_any",
    "get_user_scope_id",
    "get_node_scope_id",
]
