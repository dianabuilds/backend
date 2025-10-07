from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from pydantic import BaseModel

from ...domain.records import AppealRecord
from ..common import isoformat_utc

JSONMapping = Mapping[str, object]


class _AttrDict(dict[str, object]):
    __slots__ = ()

    def __getattr__(self, item: str) -> object:
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - parity with dict behaviour
            raise AttributeError(item) from exc


def record_to_dto(record: AppealRecord, reports: Sequence[JSONMapping]) -> _AttrDict:
    return _AttrDict(
        {
            "id": record.id,
            "status": record.status,
            "user_id": record.user_id,
            "target_type": record.target_type,
            "target_id": record.target_id,
            "text": record.text,
            "created_at": isoformat_utc(record.created_at),
            "decided_at": isoformat_utc(record.decided_at),
            "decided_by": record.decided_by,
            "decision_reason": record.decision_reason,
            "reports": [
                {str(key): value for key, value in report.items()} for report in reports
            ],
            "meta": dict(record.meta),
        }
    )


def _to_mapping(dto: object) -> dict[str, object]:
    if isinstance(dto, BaseModel):
        data = dto.model_dump()
        return {str(key): value for key, value in data.items()}
    if isinstance(dto, Mapping):
        return {str(key): value for key, value in dto.items()}
    raise TypeError(f"Unsupported appeal DTO type: {type(dto)!r}")


def build_list_response(
    items: Sequence[object], *, next_cursor: str | None
) -> dict[str, object]:
    data = [_to_mapping(item) for item in items]
    return {"items": data, "next_cursor": next_cursor}


def build_appeals_list_response(
    items: Sequence[object], *, next_cursor: str | None
) -> dict[str, object]:
    return build_list_response(items, next_cursor=next_cursor)


def merge_appeal_with_db(dto: object, db_record: JSONMapping | None) -> _AttrDict:
    base = _to_mapping(dto)
    if not db_record:
        return _AttrDict(base)

    merged = dict(base)
    status = db_record.get("status")
    if isinstance(status, str):
        merged["status"] = status
    decided_at = db_record.get("decided_at")
    if isinstance(decided_at, datetime):
        merged["decided_at"] = isoformat_utc(decided_at)
    elif isinstance(decided_at, str) and decided_at:
        merged["decided_at"] = decided_at
    decided_by = db_record.get("decided_by")
    if decided_by is not None:
        merged["decided_by"] = decided_by
    reason = db_record.get("decision_reason")
    if reason is not None:
        merged["decision_reason"] = reason
    meta_update = db_record.get("meta")
    if isinstance(meta_update, Mapping):
        current_meta = merged.get("meta")
        if isinstance(current_meta, Mapping):
            meta = {str(key): value for key, value in current_meta.items()}
        else:
            meta = {}
        meta.update({str(key): value for key, value in meta_update.items()})
        merged["meta"] = meta
    merged["db_state"] = {str(key): value for key, value in db_record.items()}
    return _AttrDict(merged)


def build_decision_response(
    appeal_id: str,
    *,
    status: str,
    decided_at: str,
    decided_by: str,
    db_record: JSONMapping | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "appeal_id": appeal_id,
        "status": status,
        "decided_at": decided_at,
        "decided_by": decided_by,
    }
    if db_record is not None:
        db_state = {str(key): value for key, value in db_record.items()}
        payload["db_state"] = db_state
        status_value = db_state.get("status", status)
        if isinstance(status_value, str):
            payload["status"] = status_value
    return payload


__all__ = [
    "build_appeals_list_response",
    "build_decision_response",
    "build_list_response",
    "merge_appeal_with_db",
    "record_to_dto",
]
