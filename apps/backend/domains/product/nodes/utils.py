from __future__ import annotations

import re
import uuid as _uuid
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from html import unescape
from typing import Any, TypeVar

ROLE_HIERARCHY = {"user": 0, "support": 1, "editor": 2, "moderator": 3, "admin": 4}


def normalize_actor_id(claims: Mapping[str, Any] | None) -> str:
    sub = str((claims or {}).get("sub") or "").strip()
    if not sub:
        return ""
    try:
        _uuid.UUID(sub)
        return sub
    except (ValueError, TypeError):
        try:
            return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"user:{sub}"))
        except Exception:  # pragma: no cover - defensive
            return ""


def get_role(claims: Mapping[str, Any] | None) -> str:
    return str((claims or {}).get("role") or "").lower()


def has_role(claims: Mapping[str, Any] | None, min_role: str) -> bool:
    return ROLE_HIERARCHY.get(get_role(claims), 0) >= ROLE_HIERARCHY.get(min_role, 0)


def require_role(claims: Mapping[str, Any] | None, min_role: str) -> None:
    if not has_role(claims, min_role):
        raise PermissionError(min_role)


T = TypeVar("T")


def first(iterable: Iterable[T]) -> T | None:
    for item in iterable:
        return item
    return None


def parse_request_datetime(raw: str) -> datetime:
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError("invalid_timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def view_stat_to_dict(stat) -> dict[str, Any]:
    return {
        "node_id": stat.node_id,
        "bucket_date": stat.bucket_date,
        "views": stat.views,
    }


def reactions_summary_to_dict(summary) -> dict[str, Any]:
    return {
        "node_id": summary.node_id,
        "totals": summary.totals,
        "user_reaction": summary.user_reaction,
    }


def comment_to_dict(comment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "node_id": comment.node_id,
        "author_id": comment.author_id,
        "parent_comment_id": comment.parent_comment_id,
        "depth": comment.depth,
        "content": comment.content,
        "status": comment.status,
        "metadata": comment.metadata,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }


def comment_ban_to_dict(ban) -> dict[str, Any]:
    return {
        "node_id": ban.node_id,
        "target_user_id": ban.target_user_id,
        "set_by": ban.set_by,
        "reason": ban.reason,
        "created_at": ban.created_at,
    }


def iso_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat()
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - defensive
            return str(value)
    return str(value)


def strip_html_summary(value: str | None, limit: int = 320) -> str:
    if not value:
        return ""
    text_value = unescape(re.sub(r"<[^>]+>", " ", str(value)))
    text_value = re.sub(r"\s+", " ", text_value).strip()
    if limit and len(text_value) > limit:
        truncated = text_value[:limit].rstrip()
        cutoff = truncated.rfind(" ")
        if cutoff > max(24, int(limit * 0.6)):
            truncated = truncated[:cutoff].rstrip()
        text_value = truncated.rstrip(",.;:-") + "..."
    return text_value
