from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypedDict, cast

from ...domain.dtos import (
    SanctionStatus,
    TicketStatus,
    UserDetail,
    UserSummary,
)
from ...domain.records import UserRecord
from ..common import isoformat_utc, resolve_iso
from ..presenters.dto_builders import (
    note_to_dto,
    report_to_dto,
    sanction_to_dto,
    ticket_to_dto,
)
from ..sanctions import get_sanctions_for_user

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService


class ModeratorNotePayload(TypedDict, total=False):
    id: str
    text: str
    author_id: str | None
    author_name: str | None
    created_at: str | None
    pinned: bool
    meta: dict[str, Any]


class UserSummaryPayload(TypedDict, total=False):
    id: str
    username: str
    email: str | None
    roles: list[str]
    status: str
    registered_at: str | None
    last_seen_at: str | None
    complaints_count: int
    notes_count: int
    sanction_count: int
    active_sanctions: list[dict[str, Any]]
    last_sanction: dict[str, Any] | None
    meta: dict[str, Any]


class UserDetailPayload(UserSummaryPayload, total=False):
    sanctions: list[dict[str, Any]]
    reports: list[dict[str, Any]]
    tickets: list[dict[str, Any]]
    notes: list[ModeratorNotePayload]


class UsersListResponse(TypedDict):
    items: list[UserSummaryPayload]
    next_cursor: str | None


class RolesUpdateResponse(TypedDict):
    user_id: str
    roles: list[str]


class SanctionResponse(TypedDict, total=False):
    id: str
    type: str
    status: str
    reason: str | None
    issued_by: str | None
    issued_at: str | None
    starts_at: str | None
    ends_at: str | None
    revoked_at: str | None
    revoked_by: str | None
    evidence: list[str]
    meta: dict[str, Any]


def _dump_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[call-arg]
    if isinstance(model, Mapping):
        return dict(model)
    return dict(model.__dict__)


def _coerce_summary_payload(data: Any) -> UserSummaryPayload:
    payload = _dump_model(data)
    return cast(UserSummaryPayload, payload)


def _coerce_detail_payload(data: Any) -> UserDetailPayload:
    payload = _dump_model(data)
    payload.setdefault("sanctions", [])
    payload.setdefault("reports", [])
    payload.setdefault("tickets", [])
    payload.setdefault("notes", [])
    return cast(UserDetailPayload, payload)


def _coerce_note_payload(data: Any) -> ModeratorNotePayload:
    payload = _dump_model(data)
    return cast(ModeratorNotePayload, payload)


def user_to_summary(
    service: PlatformModerationService, record: UserRecord
) -> UserSummary:
    sanctions = get_sanctions_for_user(service, record)
    iso = resolve_iso(service)
    active_dtos = [
        sanction_to_dto(s, iso=iso)
        for s in sanctions
        if s.status == SanctionStatus.active
    ]
    last_dto = sanction_to_dto(sanctions[0], iso=iso) if sanctions else None
    open_tickets = sum(
        1
        for tid in record.ticket_ids
        if tid in service._tickets
        and service._tickets[tid].status
        not in {TicketStatus.solved, TicketStatus.closed}
    )
    appeals_active = sum(
        1
        for appeal in service._appeals.values()
        if appeal.user_id == record.id
        and appeal.status.lower() in {"new", "pending", "review"}
    )
    return UserSummary(
        id=record.id,
        username=record.username,
        email=record.email,
        roles=list(record.roles),
        status=record.status,
        registered_at=isoformat_utc(record.registered_at),
        last_seen_at=isoformat_utc(record.last_seen_at),
        complaints_count=len(record.report_ids),
        notes_count=len(record.note_ids),
        sanction_count=len(record.sanction_ids),
        active_sanctions=active_dtos,
        last_sanction=last_dto,
        meta={
            "tickets_open": open_tickets,
            "appeals_active": appeals_active,
        },
    )


def user_to_detail(
    service: PlatformModerationService, record: UserRecord
) -> UserDetail:
    base = user_to_summary(service, record)
    iso = resolve_iso(service)
    sanctions = [
        sanction_to_dto(s, iso=iso) for s in get_sanctions_for_user(service, record)
    ]
    reports = [
        report_to_dto(service._reports[rid], iso=iso)
        for rid in record.report_ids
        if rid in service._reports
    ]
    resolver = (
        service._ticket_messages.get
        if hasattr(service, "_ticket_messages")
        else (lambda _mid: None)
    )
    tickets = [
        ticket_to_dto(
            service._tickets[tid],
            resolve_message=resolver,
            iso=iso,
        )
        for tid in record.ticket_ids
        if tid in service._tickets
    ]
    notes = [
        note_to_dto(service._notes[nid], iso=iso)
        for nid in record.note_ids
        if nid in service._notes
    ]
    data = base.model_dump()
    data.update(
        {
            "sanctions": sanctions,
            "reports": reports,
            "tickets": tickets,
            "notes": notes,
        }
    )
    return UserDetail(**data)


def build_list_response(
    items: Iterable[Any],
    *,
    next_cursor: str | None = None,
) -> UsersListResponse:
    summaries = [_coerce_summary_payload(item) for item in items]
    return {"items": summaries, "next_cursor": next_cursor}


def build_detail_response(detail: Any) -> UserDetailPayload:
    return _coerce_detail_payload(detail)


def build_roles_response(user_id: str, roles: Sequence[str]) -> RolesUpdateResponse:
    return {"user_id": user_id, "roles": list(roles)}


def build_sanction_response(
    sanction: Any,
    *,
    warnings_count: int | None = None,
) -> SanctionResponse:
    payload = _dump_model(sanction)
    meta = dict(payload.get("meta") or {})
    if warnings_count is not None:
        meta.setdefault("warnings_count", warnings_count)
    payload["meta"] = meta
    return cast(SanctionResponse, payload)


def build_note_response(note: Any) -> ModeratorNotePayload:
    return _coerce_note_payload(note)


__all__ = [
    "ModeratorNotePayload",
    "RolesUpdateResponse",
    "SanctionResponse",
    "UserDetailPayload",
    "UserSummaryPayload",
    "UsersListResponse",
    "build_detail_response",
    "build_list_response",
    "build_note_response",
    "build_roles_response",
    "build_sanction_response",
    "user_to_detail",
    "user_to_summary",
]
