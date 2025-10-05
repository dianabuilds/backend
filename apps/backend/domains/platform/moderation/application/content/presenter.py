from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ...domain.dtos import ContentStatus, ContentSummary
from ...domain.records import ContentRecord
from ..common import isoformat_utc


def record_to_summary(
    record: ContentRecord, *, reports: list[dict[str, Any]]
) -> ContentSummary:
    return ContentSummary(
        id=record.id,
        type=record.content_type,
        author_id=record.author_id,
        created_at=isoformat_utc(record.created_at),
        preview=record.preview,
        ai_labels=list(record.ai_labels),
        complaints_count=len(record.report_ids),
        status=record.status,
        moderation_history=list(record.moderation_history),
        reports=reports,
        meta=dict(record.meta),
    )


def build_queue_response(
    items: Sequence[Any], *, next_cursor: str | None
) -> dict[str, Any]:
    return {"items": items, "next_cursor": next_cursor}


def merge_summary_with_db(
    summary: ContentSummary, db_info: dict[str, Any] | None
) -> ContentSummary:
    """Merge DB snapshot into content summary while preserving model type."""
    if not db_info:
        return summary

    update: dict[str, Any] = {}
    author_id = db_info.get("author_id")
    if author_id:
        update["author_id"] = author_id
    created_at = db_info.get("created_at")
    if created_at:
        update["created_at"] = created_at
    title = db_info.get("title")
    if title:
        update["preview"] = title

    status_source = db_info.get("moderation_status") or db_info.get("status")
    if status_source:
        try:
            update["status"] = ContentStatus(status_source)
        except ValueError:
            update["status"] = summary.status

    history = db_info.get("moderation_history")
    if history:
        update["moderation_history"] = list(history)

    meta = dict(summary.meta)
    if status_source:
        meta["moderation_status"] = status_source
    node_status = db_info.get("node_status")
    if node_status:
        meta["node_status"] = node_status
    status_updated = db_info.get("moderation_status_updated_at")
    if status_updated:
        meta["moderation_status_updated_at"] = status_updated
    if meta != summary.meta:
        update["meta"] = meta

    return summary.model_copy(update=update)


def decorate_decision_response(
    content_id: str, result: dict[str, Any]
) -> dict[str, Any]:
    response = {"content_id": content_id, **result}
    db_record = response.pop("db_record", None)
    if db_record:
        response["moderation_status"] = db_record.get("status")
        history_entry = db_record.get("history_entry")
        if history_entry:
            decision = response.setdefault("decision", result.get("decision", {}))
            decision.setdefault("decided_at", history_entry.get("decided_at"))
            decision.setdefault("status", history_entry.get("status"))
        response["db_state"] = db_record
    return response


__all__ = [
    "build_queue_response",
    "decorate_decision_response",
    "merge_summary_with_db",
    "record_to_summary",
    "build_decision_response",
]


def build_decision_response(
    content_id: str,
    *,
    status: str,
    decision: Mapping[str, Any],
    db_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "decision": dict(decision),
    }
    if db_record is not None:
        result["db_record"] = dict(db_record)
    return decorate_decision_response(content_id, result)
