from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...domain.records import AppealRecord
from ..common import isoformat_utc


class _AttrDict(dict[str, Any]):
    __slots__ = ()

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:  # pragma: no cover - parity with dict behaviour
            raise AttributeError(item) from exc


def record_to_dto(record: AppealRecord, reports: list[dict[str, Any]]) -> _AttrDict:
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
            "reports": reports,
            "meta": dict(record.meta),
        }
    )


def _to_mapping(dto: Any) -> dict[str, Any]:
    if hasattr(dto, "model_dump"):
        return dto.model_dump()  # type: ignore[no-any-return]
    if isinstance(dto, Mapping):
        return dict(dto)
    raise TypeError(f"Unsupported appeal DTO type: {type(dto)!r}")


def build_list_response(items: list[Any], *, next_cursor: str | None) -> dict[str, Any]:
    data = [_to_mapping(item) for item in items]
    return {"items": data, "next_cursor": next_cursor}


def build_appeals_list_response(
    items: list[Any], *, next_cursor: str | None
) -> dict[str, Any]:
    return build_list_response(items, next_cursor=next_cursor)


def merge_appeal_with_db(dto: Any, db_record: Mapping[str, Any] | None) -> _AttrDict:
    base = _to_mapping(dto)
    if not db_record:
        return _AttrDict(base)

    merged = dict(base)
    merged["status"] = db_record.get("status", merged.get("status"))
    decided_at = db_record.get("decided_at")
    if decided_at is not None:
        merged["decided_at"] = isoformat_utc(decided_at)
    decided_by = db_record.get("decided_by")
    if decided_by is not None:
        merged["decided_by"] = decided_by
    reason = db_record.get("decision_reason")
    if reason is not None:
        merged["decision_reason"] = reason
    meta_update = db_record.get("meta")
    if isinstance(meta_update, Mapping):
        meta = dict(merged.get("meta") or {})
        meta.update(meta_update)
        merged["meta"] = meta
    merged["db_state"] = dict(db_record)
    return _AttrDict(merged)


def build_decision_response(
    appeal_id: str,
    *,
    status: str,
    decided_at: str,
    decided_by: str,
    db_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "appeal_id": appeal_id,
        "status": status,
        "decided_at": decided_at,
        "decided_by": decided_by,
    }
    if db_record is not None:
        db_state: dict[str, Any] = dict(db_record)
        payload["db_state"] = db_state
        status_value = db_state.get("status", status)
        payload["status"] = status_value if isinstance(status_value, str) else status
    return payload


__all__ = [
    "build_appeals_list_response",
    "build_decision_response",
    "build_list_response",
    "merge_appeal_with_db",
    "record_to_dto",
]
