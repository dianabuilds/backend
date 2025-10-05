from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from ..domain.dtos import (
    ModeratorNoteDTO,
    SanctionDTO,
    SanctionStatus,
    SanctionType,
)
from ..domain.records import ModeratorNoteRecord, SanctionRecord, UserRecord
from .common import parse_iso_datetime, resolve_iso
from .presenters.dto_builders import note_to_dto, sanction_to_dto

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from .service import PlatformModerationService

logger = logging.getLogger(__name__)


def _create_sanction(
    service: PlatformModerationService,
    user: UserRecord,
    *,
    stype: SanctionType,
    status: SanctionStatus,
    reason: str | None,
    issued_by: str | None,
    issued_at: datetime,
    starts_at: datetime,
    ends_at: datetime | None = None,
    evidence: Iterable[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> SanctionRecord:
    sanction = SanctionRecord(
        id=service._generate_id("san"),
        user_id=user.id,
        type=stype,
        status=status,
        reason=reason,
        issued_by=issued_by,
        issued_at=issued_at,
        starts_at=starts_at,
        ends_at=ends_at,
        evidence=list(evidence or []),
        meta=dict(meta or {}),
    )
    service._sanctions[sanction.id] = sanction
    user.sanction_ids.insert(0, sanction.id)
    if sanction.type == SanctionType.ban and sanction.status == SanctionStatus.active:
        user.status = "banned"
    return sanction


def _create_note(
    service: PlatformModerationService,
    user: UserRecord,
    *,
    text: str,
    author_id: str | None,
    author_name: str | None,
    pinned: bool = False,
    created_at: datetime | None = None,
    meta: dict[str, Any] | None = None,
) -> ModeratorNoteRecord:
    note = ModeratorNoteRecord(
        id=service._generate_id("note"),
        user_id=user.id,
        text=text,
        created_at=created_at or service._now(),
        author_id=author_id,
        author_name=author_name,
        pinned=pinned,
        meta=dict(meta or {}),
    )
    service._notes[note.id] = note
    user.note_ids.insert(0, note.id)
    return note


def get_sanctions_for_user(
    service: PlatformModerationService, user: UserRecord
) -> list[SanctionRecord]:
    return sorted(
        [
            service._sanctions[sid]
            for sid in user.sanction_ids
            if sid in service._sanctions
        ],
        key=lambda s: s.issued_at,
        reverse=True,
    )


async def issue_sanction(
    service: PlatformModerationService,
    user_id: str,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
    idempotency_key: str | None = None,
) -> SanctionDTO:
    async with service._lock:
        user = service._users.get(user_id)
        if not user:
            raise KeyError(user_id)
        if idempotency_key and idempotency_key in service._idempotency:
            sid = service._idempotency[idempotency_key]
            sanction = service._sanctions.get(sid)
            if sanction:
                return sanction_to_dto(sanction, iso=resolve_iso(service))
        try:
            stype = SanctionType(str(body.get("type", SanctionType.ban.value)))
        except ValueError as exc:
            raise ValueError("invalid_sanction_type") from exc
        status_value = body.get("status")
        status = (
            SanctionStatus(str(status_value)) if status_value else SanctionStatus.active
        )
        now = service._now()
        starts_at = parse_iso_datetime(body.get("starts_at")) or now
        ends_at = parse_iso_datetime(body.get("ends_at") or body.get("expires_at"))
        duration_hours = body.get("duration_hours")
        if ends_at is None and duration_hours is not None:
            try:
                ends_at = starts_at + timedelta(hours=float(duration_hours))
            except (TypeError, ValueError, OverflowError) as exc:
                logger.warning("Invalid sanction duration %r: %s", duration_hours, exc)
                ends_at = None
        if ends_at and ends_at <= now and status == SanctionStatus.active:
            status = SanctionStatus.expired
        sanction = _create_sanction(
            service,
            user,
            stype=stype,
            status=status,
            reason=str(body.get("reason") or None),
            issued_by=body.get("issued_by") or actor_id or "system",
            issued_at=now,
            starts_at=starts_at,
            ends_at=ends_at,
            evidence=body.get("evidence"),
            meta=body.get("meta"),
        )
        if idempotency_key:
            service._idempotency[idempotency_key] = sanction.id
        if stype == SanctionType.warning and sanction.status == SanctionStatus.active:
            since = now - timedelta(days=10)
            recent = sum(
                1
                for sid in user.sanction_ids
                if (
                    (s := service._sanctions.get(sid))
                    and s.type == SanctionType.warning
                    and s.status == SanctionStatus.active
                    and s.issued_at >= since
                )
            )
            if recent >= 3:
                _create_sanction(
                    service,
                    user,
                    stype=SanctionType.ban,
                    status=SanctionStatus.active,
                    reason=f"auto_ban_three_warnings ({recent}/3)",
                    issued_by=actor_id or "system",
                    issued_at=now,
                    starts_at=now,
                    ends_at=None,
                    evidence=None,
                    meta={
                        "source": "auto_ban",
                        "window_days": 10,
                        "warnings_count": recent,
                    },
                )
        return sanction_to_dto(sanction, iso=resolve_iso(service))


async def update_sanction(
    service: PlatformModerationService,
    user_id: str,
    sanction_id: str,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
) -> SanctionDTO:
    async with service._lock:
        sanction = service._sanctions.get(sanction_id)
        if not sanction or sanction.user_id != user_id:
            raise KeyError(sanction_id)
        if "status" in body and body["status"] is not None:
            try:
                sanction.status = SanctionStatus(str(body["status"]))
            except ValueError as exc:
                raise ValueError("invalid_sanction_status") from exc
        if "reason" in body:
            sanction.reason = str(body.get("reason") or None)
        if "ends_at" in body or "expires_at" in body:
            sanction.ends_at = parse_iso_datetime(
                body.get("ends_at") or body.get("expires_at")
            )
        if "evidence" in body:
            sanction.evidence = list(body.get("evidence") or [])
        metadata = body.get("meta") or body.get("metadata")
        if metadata:
            sanction.meta.update(dict(metadata))
        if body.get("revoke") or (body.get("status") == SanctionStatus.canceled.value):
            sanction.status = SanctionStatus.canceled
            sanction.revoked_at = service._now()
            sanction.revoked_by = actor_id or body.get("revoked_by") or "system"
        if (
            sanction.ends_at
            and sanction.ends_at <= service._now()
            and sanction.status == SanctionStatus.active
        ):
            sanction.status = SanctionStatus.expired
        user = service._users.get(user_id)
        if user and sanction.type == SanctionType.ban:
            has_active_ban = any(
                service._sanctions[sid].status == SanctionStatus.active
                and service._sanctions[sid].type == SanctionType.ban
                for sid in user.sanction_ids
                if sid in service._sanctions
            )
            user.status = "banned" if has_active_ban else "active"
        return sanction_to_dto(sanction, iso=resolve_iso(service))


async def add_note(
    service: PlatformModerationService,
    user_id: str,
    body: dict[str, Any],
    *,
    actor_id: str | None = None,
    actor_name: str | None = None,
) -> ModeratorNoteDTO:
    async with service._lock:
        user = service._users.get(user_id)
        if not user:
            raise KeyError(user_id)
        note = _create_note(
            service,
            user,
            text=str(body.get("text") or ""),
            author_id=body.get("author_id") or actor_id,
            author_name=body.get("author_name") or actor_name,
            pinned=bool(body.get("pinned") or False),
            created_at=parse_iso_datetime(body.get("created_at")),
            meta=body.get("meta"),
        )
        return note_to_dto(note, iso=resolve_iso(service))


__all__ = [
    "issue_sanction",
    "update_sanction",
    "add_note",
    "get_sanctions_for_user",
]
