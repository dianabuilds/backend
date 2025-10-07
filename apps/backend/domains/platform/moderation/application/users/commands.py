from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

from ...domain.records import UserRecord
from .exceptions import ModerationUserError, UserNotFoundError
from .presenter import (
    ModeratorNotePayload,
    RolesUpdateResponse,
    SanctionResponse,
    build_note_response,
    build_roles_response,
    build_sanction_response,
)
from .repository import ModerationUsersRepository, create_repository

if TYPE_CHECKING:  # pragma: no cover
    from .service import PlatformModerationService

logger = logging.getLogger(__name__)


async def ensure_user_stub(
    service: PlatformModerationService,
    *,
    user_id: str,
    username: str,
    email: str | None = None,
) -> None:
    """Ensure that the in-memory snapshot has at least a stub for the user."""

    async with service._lock:
        if user_id in service._users:
            return
        service._users[user_id] = UserRecord(
            id=user_id,
            username=username or user_id,
            email=email,
            roles=["User"],
            status="active",
            registered_at=service._now(),
        )


async def update_roles(
    service: PlatformModerationService,
    user_id: str,
    add: Iterable[str],
    remove: Iterable[str],
) -> list[str]:
    """Internal helper used by the service to sync the cache."""

    async with service._lock:
        record = service._users.get(user_id)
        if not record:
            raise KeyError(user_id)
        current = {r for r in record.roles}
        for role in remove:
            if role is not None:
                current.discard(str(role))
        for role in add:
            if role is not None:
                current.add(str(role))
        record.roles = sorted(current, key=lambda r: r.lower())
        return list(record.roles)


def _resolve_repository(
    settings: Any | None,
    repository: ModerationUsersRepository | None,
) -> ModerationUsersRepository | None:
    if repository is not None:
        return repository
    if settings is None:
        return None
    return create_repository(settings)


async def update_roles_command(
    service: PlatformModerationService,
    user_id: str,
    body: Mapping[str, Any],
    *,
    settings: Any | None = None,
    repository: ModerationUsersRepository | None = None,
) -> RolesUpdateResponse:
    """Update roles via SQL and mirror the change in the service cache."""

    repo = _resolve_repository(settings, repository)
    if repo is None:
        raise ModerationUserError(code="roles_update_failed", status_code=500)

    add_raw = body.get("add", [])
    remove_raw = body.get("remove", [])
    if not isinstance(add_raw, Iterable) or not isinstance(remove_raw, Iterable):
        raise ModerationUserError(code="roles_update_failed", status_code=400)

    add = [str(role).strip().lower() for role in add_raw if role is not None]
    remove = [str(role).strip().lower() for role in remove_raw if role is not None]

    roles = await repo.update_roles(user_id, add=add, remove=remove)

    try:
        await service.update_roles(user_id, add=add, remove=remove)
    except KeyError:
        logger.debug("moderation users: service cache missing %s", user_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(
            "moderation users: unable to sync service roles for %s: %s",
            user_id,
            exc,
        )

    return build_roles_response(user_id, roles)


async def issue_sanction(
    service: PlatformModerationService,
    user_id: str,
    body: Mapping[str, Any],
    *,
    settings: Any | None = None,
    notifications: Any | None = None,
    repository: ModerationUsersRepository | None = None,
    idempotency_key: str | None = None,
) -> SanctionResponse:
    """Issue a sanction, optionally persisting it via SQL and notifying the user."""

    repo = _resolve_repository(settings, repository)

    if repo is not None:
        try:
            stub = await repo.bootstrap_user_stub(user_id)
        except UserNotFoundError:
            raise
        await ensure_user_stub(
            service,
            user_id=stub["id"],
            username=stub["username"],
            email=stub.get("email"),
        )
    else:
        await ensure_user_stub(service, user_id=user_id, username=user_id, email=None)

    actor_id = body.get("issued_by") or body.get("actor_id")
    try:
        sanction = await service.issue_sanction(
            user_id,
            body,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
        )
    except KeyError as exc:
        raise UserNotFoundError() from exc
    except ValueError as exc:
        raise ModerationUserError(
            code=str(exc) or "sanction_invalid",
            status_code=400,
            message=str(exc) or "sanction_invalid",
        ) from exc

    sanction_payload = (
        sanction.model_dump() if hasattr(sanction, "model_dump") else dict(sanction)
    )
    warnings_count = 0
    auto_ban_created = False
    if repo is not None:
        warnings_count, auto_ban_created = await repo.persist_sanction(
            user_id,
            sanction_payload,
            actor_id=actor_id,
        )

    if notifications is not None:
        try:
            notify = notifications
            sanction_type = sanction_payload.get("type")
            reason = sanction_payload.get("reason")
            if sanction_type == "warning":
                await notify.create_notification(
                    user_id=user_id,
                    title="Warning",
                    message=str(reason or "You have received a warning"),
                    type_="warning",
                )
                if auto_ban_created:
                    await notify.create_notification(
                        user_id=user_id,
                        title="Account banned",
                        message="You have been banned due to multiple warnings.",
                        type_="ban",
                    )
            elif sanction_type == "ban":
                await notify.create_notification(
                    user_id=user_id,
                    title="Account banned",
                    message=str(reason or "Your account has been banned"),
                    type_="ban",
                )
        except (AttributeError, RuntimeError, TypeError) as exc:  # pragma: no cover
            logger.debug(
                "moderation users: notification dispatch failed for %s: %s",
                user_id,
                exc,
            )

    return build_sanction_response(sanction_payload, warnings_count=warnings_count)


async def update_sanction(
    service: PlatformModerationService,
    user_id: str,
    sanction_id: str,
    body: Mapping[str, Any],
) -> SanctionResponse:
    try:
        sanction = await service.update_sanction(
            user_id,
            sanction_id,
            body,
            actor_id=body.get("actor_id"),
        )
    except KeyError as exc:
        raise ModerationUserError(
            code="sanction_not_found",
            status_code=404,
            message="sanction_not_found",
        ) from exc
    except ValueError as exc:
        raise ModerationUserError(
            code=str(exc) or "sanction_invalid",
            status_code=400,
            message=str(exc) or "sanction_invalid",
        ) from exc

    payload = (
        sanction.model_dump() if hasattr(sanction, "model_dump") else dict(sanction)
    )
    return build_sanction_response(payload)


async def add_note(
    service: PlatformModerationService,
    user_id: str,
    body: Mapping[str, Any],
    *,
    settings: Any | None = None,
    repository: ModerationUsersRepository | None = None,
) -> ModeratorNotePayload:
    text_value = str(body.get("text") or "").strip()
    if not text_value:
        raise ModerationUserError(code="text_required", status_code=400)

    pinned = bool(body.get("pinned") or False)
    raw_meta = body.get("meta")
    meta = dict(raw_meta) if isinstance(raw_meta, Mapping) else {}
    author_id = body.get("author_id")
    author_name = body.get("author_name")

    repo = _resolve_repository(settings, repository)
    if repo is not None:
        try:
            note_row = await repo.add_note(
                user_id,
                text=text_value,
                author_id=author_id,
                author_name=author_name,
                pinned=pinned,
                meta=meta,
            )
        except UserNotFoundError:
            raise
        except ModerationUserError:
            raise
        if note_row is not None:
            return build_note_response(note_row)

    try:
        await service.ensure_user_stub(user_id=user_id, username=user_id, email=None)
    except Exception:  # pragma: no cover - service bootstrap failures ignored
        pass

    try:
        note = await service.add_note(
            user_id,
            {
                "text": text_value,
                "author_id": author_id,
                "author_name": author_name,
                "pinned": pinned,
                "meta": meta,
            },
            actor_id=author_id,
            actor_name=author_name,
        )
    except KeyError as exc:
        raise UserNotFoundError() from exc

    payload = note.model_dump() if hasattr(note, "model_dump") else dict(note)
    return build_note_response(payload)


__all__ = [
    "add_note",
    "ensure_user_stub",
    "issue_sanction",
    "update_roles",
    "update_roles_command",
    "update_sanction",
]
