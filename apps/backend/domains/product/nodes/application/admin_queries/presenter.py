"""Presentation helpers for admin node use-cases."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from io import StringIO
from typing import Any

from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
)

_ALLOWED_MODERATION_STATUSES = {
    "pending",
    "resolved",
    "hidden",
    "restricted",
    "escalated",
}
_DECISION_STATUS_MAP = {
    "keep": "resolved",
    "hide": "hidden",
    "delete": "hidden",
    "restrict": "restricted",
    "escalate": "escalated",
    "review": "pending",
}
_COMMENT_STATUS_ORDER = ["pending", "published", "hidden", "deleted", "blocked"]
_COMMENT_STATUS_SET = set(_COMMENT_STATUS_ORDER)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return _iso(parsed)


def _normalize_moderation_status(value: Any) -> str:
    try:
        result = str(value or "").strip().lower()
    except (AttributeError, TypeError, ValueError):
        result = ""
    if result not in _ALLOWED_MODERATION_STATUSES:
        return "pending"
    return result


def _decision_to_status(action: str) -> str:
    return _DECISION_STATUS_MAP.get(action, "pending")


def _normalize_comment_status_filter(
    statuses: Any,
    *,
    include_deleted: bool,
) -> list[str]:
    if not statuses:
        base = list(_COMMENT_STATUS_ORDER)
        if not include_deleted:
            base = [status for status in base if status != "deleted"]
        return base
    result: list[str] = []
    seen: set[str] = set()
    values = statuses
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    for raw in values:
        try:
            normalized = str(raw or "").strip().lower()
        except (TypeError, ValueError):
            continue
        if normalized == "deleted" and not include_deleted:
            continue
        if normalized in _COMMENT_STATUS_SET and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    if not result:
        base = list(_COMMENT_STATUS_ORDER)
        if not include_deleted:
            base = [status for status in base if status != "deleted"]
        return base
    return result


def _coerce_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        try:
            return json.loads(json.dumps(raw))
        except (TypeError, ValueError):
            return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except ValueError:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return {}
    return {}


def _extract_comment_history(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    history_raw = metadata.get("history")
    history: list[dict[str, Any]] = []
    if isinstance(history_raw, list):
        for entry in history_raw:
            if not isinstance(entry, dict):
                continue
            record = {
                "status": str(entry.get("status") or ""),
                "actor_id": (
                    str(entry.get("actor_id")) if entry.get("actor_id") else None
                ),
                "reason": entry.get("reason"),
                "at": _iso(entry.get("at")),
            }
            history.append(record)
    return history


def _comment_record_to_payload(
    *,
    comment_id: int,
    node_id: int,
    author_id: str,
    parent_comment_id: int | None,
    depth: int,
    content: str,
    status: str,
    metadata: Any,
    created_at: Any,
    updated_at: Any,
    children_count: int | None = None,
) -> dict[str, Any]:
    meta = _coerce_metadata(metadata)
    history = _extract_comment_history(meta)
    payload: dict[str, Any] = {
        "id": str(comment_id),
        "node_id": str(node_id),
        "author_id": str(author_id),
        "parent_comment_id": (
            str(parent_comment_id) if parent_comment_id is not None else None
        ),
        "depth": int(depth),
        "content": content,
        "status": str(status),
        "metadata": meta,
        "history": history,
        "created_at": _iso(created_at),
        "updated_at": _iso(updated_at),
    }
    if children_count is not None:
        payload["children_count"] = int(children_count)
    return payload


def _comment_dto_to_dict(
    dto: NodeCommentDTO, *, children_count: int | None = None
) -> dict[str, Any]:
    return _comment_record_to_payload(
        comment_id=dto.id,
        node_id=dto.node_id,
        author_id=dto.author_id,
        parent_comment_id=dto.parent_comment_id,
        depth=dto.depth,
        content=dto.content,
        status=dto.status,
        metadata=dto.metadata,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        children_count=children_count,
    )


def _comment_row_to_dict(row) -> dict[str, Any]:
    parent_raw = row.get("parent_comment_id")
    parent_id = None if parent_raw is None else int(parent_raw)
    children_raw = row.get("children_count")
    children_count = None
    if children_raw is not None:
        try:
            children_count = int(children_raw)
        except (TypeError, ValueError):
            children_count = None
    return _comment_record_to_payload(
        comment_id=int(row["id"]),
        node_id=int(row["node_id"]),
        author_id=str(row.get("author_id")),
        parent_comment_id=parent_id,
        depth=int(row["depth"]),
        content=row.get("content"),
        status=str(row.get("status")),
        metadata=row.get("metadata"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        children_count=children_count,
    )


def _ban_to_dict(ban: NodeCommentBanDTO) -> dict[str, Any]:
    return {
        "node_id": str(ban.node_id),
        "target_user_id": ban.target_user_id,
        "set_by": ban.set_by,
        "reason": ban.reason,
        "created_at": _iso(ban.created_at),
    }


def _status_summary_from_counts(counts: dict[str, int]) -> dict[str, Any]:
    summary = {status: int(counts.get(status, 0)) for status in _COMMENT_STATUS_ORDER}
    total = sum(summary.values())
    return {"total": total, "by_status": summary}


def _analytics_to_csv(payload: dict[str, Any]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["bucket_date", "views", "total_likes", "total_comments"])
    totals = payload.get("reactions", {}).get("totals", {})
    total_likes = sum(int(value) for value in totals.values())
    total_comments = int(payload.get("comments", {}).get("total") or 0)
    for bucket in payload.get("views", {}).get("buckets", []):
        writer.writerow(
            [
                bucket.get("bucket_date"),
                bucket.get("views"),
                total_likes,
                total_comments,
            ]
        )
    return buffer.getvalue()


def _build_moderation_detail(
    row: dict[str, Any], history_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    moderation_status = _normalize_moderation_status(row.get("moderation_status"))
    history: list[dict[str, Any]] = []
    for entry in history_rows:
        history.append(
            {
                "action": entry.get("action"),
                "status": _normalize_moderation_status(entry.get("status")),
                "reason": entry.get("reason"),
                "actor": entry.get("actor_id"),
                "decided_at": _iso(entry.get("decided_at")),
            }
        )
    meta: dict[str, Any] = {
        "node_status": row.get("status"),
        "moderation_status": moderation_status,
        "moderation_status_updated_at": _iso(row.get("moderation_status_updated_at")),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "slug": row.get("slug"),
        "is_public": row.get("is_public"),
    }
    return {
        "id": str(row.get("id")),
        "type": "node",
        "author_id": row.get("author_id"),
        "preview": row.get("title"),
        "status": moderation_status,
        "moderation_history": history,
        "meta": meta,
        "reports": [],
    }


__all__ = [
    "_DECISION_STATUS_MAP",
    "_analytics_to_csv",
    "_ban_to_dict",
    "_build_moderation_detail",
    "_comment_dto_to_dict",
    "_comment_record_to_payload",
    "_comment_row_to_dict",
    "_decision_to_status",
    "_normalize_comment_status_filter",
    "_normalize_moderation_status",
    "_status_summary_from_counts",
    "_iso",
]
