from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import TypeAlias, TypedDict, cast

from ...domain.dtos import ContentStatus, ContentSummary, ReportDTO
from ...domain.records import ContentRecord
from ..common import isoformat_utc

JSONMapping: TypeAlias = Mapping[str, object]
QueueMapping: TypeAlias = Mapping[str, object]
QueueItem: TypeAlias = ContentSummary | QueueMapping


class QueueResponse(TypedDict):
    items: list[dict[str, object]]
    next_cursor: str | None


class DecisionResponse(TypedDict, total=False):
    content_id: str
    status: str
    decision: dict[str, object]
    moderation_status: str
    db_state: dict[str, object]


class DecisionPayload(TypedDict, total=False):
    status: str
    decision: dict[str, object]
    db_record: dict[str, object]


def record_to_summary(
    record: ContentRecord, *, reports: Sequence[JSONMapping]
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
        reports=[ReportDTO.model_validate(dict(report)) for report in reports],
        meta=dict(record.meta),
    )


def _normalize_queue_item(item: QueueItem) -> dict[str, object]:
    if isinstance(item, ContentSummary):
        return cast(dict[str, object], item.model_dump())
    return {str(key): value for key, value in item.items()}


def build_queue_response(
    items: Sequence[QueueItem], *, next_cursor: str | None
) -> QueueResponse:
    normalized = [_normalize_queue_item(item) for item in items]
    return cast(QueueResponse, {"items": normalized, "next_cursor": next_cursor})


def merge_summary_with_db(
    summary: ContentSummary, db_info: JSONMapping | None
) -> ContentSummary:
    """Merge DB snapshot into content summary while preserving model type."""
    if not db_info:
        return summary

    update: dict[str, object] = {}
    author_id = db_info.get("author_id")
    if isinstance(author_id, str) and author_id:
        update["author_id"] = author_id
    created_at = db_info.get("created_at")
    if isinstance(created_at, str) and created_at:
        update["created_at"] = created_at
    title = db_info.get("title")
    if isinstance(title, str) and title:
        update["preview"] = title

    status_source = db_info.get("moderation_status") or db_info.get("status")
    if status_source:
        try:
            update["status"] = ContentStatus(str(status_source))
        except ValueError:
            update["status"] = summary.status

    history = db_info.get("moderation_history")
    if isinstance(history, Sequence):
        update["moderation_history"] = list(history)

    meta: dict[str, object] = dict(summary.meta)
    if status_source:
        meta["moderation_status"] = status_source
    meta_update = db_info.get("meta")
    if isinstance(meta_update, Mapping):
        meta.update({str(key): value for key, value in meta_update.items()})
    node_status = db_info.get("node_status")
    if node_status is not None:
        meta["node_status"] = node_status
    status_updated = db_info.get("moderation_status_updated_at")
    if status_updated is not None:
        meta["moderation_status_updated_at"] = status_updated
    if meta != summary.meta:
        update["meta"] = meta

    return summary.model_copy(update=update)


def decorate_decision_response(
    content_id: str, result: Mapping[str, object]
) -> DecisionResponse:
    response: dict[str, object] = {"content_id": content_id}
    intermediate = dict(result)
    db_record = intermediate.pop("db_record", None)
    decision_payload = intermediate.get("decision")
    if isinstance(decision_payload, Mapping):
        intermediate["decision"] = dict(decision_payload)
    response.update(intermediate)

    if isinstance(db_record, Mapping):
        db_state = dict(db_record)
        response["db_state"] = db_state
        status_value = db_state.get("status")
        if isinstance(status_value, str):
            response["moderation_status"] = status_value
        history_entry = db_state.get("history_entry")
        decision = response.setdefault("decision", {})
        if isinstance(decision, MutableMapping) and isinstance(history_entry, Mapping):
            decision.setdefault("decided_at", history_entry.get("decided_at"))
            decision.setdefault("status", history_entry.get("status"))

    return cast(DecisionResponse, response)


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
    decision: Mapping[str, object],
    db_record: Mapping[str, object] | None = None,
) -> DecisionResponse:
    payload: DecisionPayload = {
        "status": status,
        "decision": dict(decision),
    }
    if db_record is not None:
        payload["db_record"] = dict(db_record)
    return decorate_decision_response(content_id, payload)
