from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.exc import SQLAlchemyError

try:  # pragma: no cover - optional dependency in tests
    from packages.core.config import to_async_dsn
    from packages.core.db import get_async_engine
except ModuleNotFoundError:  # pragma: no cover
    to_async_dsn = get_async_engine = None

from packages.core.testing import is_test_mode

from ...domain.dtos import ModeratorNoteDTO
from .exceptions import ModerationUserError, UserNotFoundError
from .queries import get_user as service_get_user
from .queries import list_users as service_list_users

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class UseCaseResult:
    payload: Any
    status_code: int = 200


def _should_use_sql(settings) -> bool:
    if settings is None:
        return False
    if is_test_mode(settings):
        return False
    return True


def _build_engine(settings, *, suffix: str) -> Any:
    if not _should_use_sql(settings):
        logger.debug("users use-case: SQL backend disabled; using in-memory mode")
        return None
    if to_async_dsn is None or get_async_engine is None:
        return None
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        logger.debug("users use-case: no database_url configured; using in-memory mode")
        return None
    try:
        dsn = to_async_dsn(database_url)
    except (TypeError, ValueError) as exc:  # pragma: no cover - config issues
        logger.debug("users use-case: invalid DSN: %s", exc)
        return None
    if not dsn:
        logger.debug(
            "users use-case: DSN normalized to empty value; using in-memory mode"
        )
        return None
    try:
        return get_async_engine(f"moderation-users-{suffix}", url=dsn, future=True)
    except (SQLAlchemyError, RuntimeError, ImportError) as exc:
        logger.warning("users use-case: failed to create engine: %s", exc)
        return None


def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _note_row_to_dict(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id")),
        "text": str(row.get("text") or ""),
        "author_id": row.get("author_id"),
        "author_name": row.get("author_name"),
        "created_at": _to_iso(row.get("created_at")),
        "pinned": bool(row.get("pinned")),
        "meta": dict(row.get("meta") or {}),
    }


def _normalise_role(value: Any) -> str:
    try:
        text = str(value or "").strip()
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("users use-case: cannot normalise role %r: %s", value, exc)
        return str(value)
    if not text:
        return "User"
    return text[:1].upper() + text[1:].lower()


async def list_users(
    service,
    settings,
    *,
    status: str | None = None,
    role: str | None = None,
    registered_from: str | None = None,
    registered_to: str | None = None,
    q: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> UseCaseResult:
    engine = _build_engine(settings, suffix="list")
    if engine is not None:
        try:
            qp = f"%{(q or '').strip()}%"
            try:
                offset = int(cursor or 0)
            except (TypeError, ValueError) as exc:
                logger.debug("moderation users: invalid cursor %r: %s", cursor, exc)
                offset = 0

            async with engine.begin() as conn:
                have_user_roles = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1 FROM information_schema.tables
                                WHERE table_schema = current_schema() AND table_name = 'user_roles'
                                LIMIT 1
                                """
                            )
                        )
                    ).first()
                )
                have_notes_table = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1 FROM information_schema.tables
                                WHERE table_schema = current_schema() AND table_name = 'moderator_user_notes'
                                LIMIT 1
                                """
                            )
                        )
                    ).first()
                )
                notes_select = (
                    "(SELECT COUNT(*) FROM moderator_user_notes mn WHERE mn.user_id = u.id) AS notes_count"
                    if have_notes_table
                    else "0 AS notes_count"
                )

                cols = (
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'users'"
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                cols_set = {str(c) for c in cols}

                name_expr_parts: list[str] = []
                if "username" in cols_set:
                    name_expr_parts.append("u.username")
                if "display_name" in cols_set:
                    name_expr_parts.append("u.display_name")
                name_expr_parts.append("u.email")
                name_expr = "COALESCE(" + ", ".join(name_expr_parts) + ")"

                order_by = (
                    "u.created_at DESC NULLS LAST, u.id DESC"
                    if "created_at" in cols_set
                    else "u.id DESC"
                )

                where_parts = [":q = ''"]
                like_exprs: list[str] = []
                if "username" in cols_set:
                    like_exprs.append("lower(COALESCE(u.username, '')) LIKE lower(:qp)")
                if "display_name" in cols_set:
                    like_exprs.append(
                        "lower(COALESCE(u.display_name, '')) LIKE lower(:qp)"
                    )
                like_exprs.append("lower(COALESCE(u.email, '')) LIKE lower(:qp)")
                where_parts.append("(" + " OR ".join(like_exprs) + ")")

                if have_user_roles:
                    roles_join = (
                        "LEFT JOIN (SELECT user_id, array_agg(role::text ORDER BY role) AS roles "
                        "FROM user_roles GROUP BY user_id) ur ON ur.user_id = u.id"
                    )
                    roles_select = "COALESCE(ur.roles, ARRAY[]::text[]) AS roles"
                else:
                    roles_join = ""
                    roles_select = (
                        "ARRAY[COALESCE(u.role::text, 'user')] AS roles"
                        if "role" in cols_set
                        else "ARRAY['user'] AS roles"
                    )

                ban_exists = (
                    "EXISTS (SELECT 1 FROM user_sanctions s WHERE s.user_id = u.id AND s.type = 'ban' "
                    "AND s.status = 'active' AND s.starts_at <= now() AND (s.ends_at IS NULL OR s.ends_at > now()))"
                )

                sql_txt = f"""
                    SELECT u.id::text AS id,
                           {name_expr} AS username,
                           u.email,
                           {roles_select},
                           {ban_exists} AS is_banned,
                           {notes_select}
                    FROM users u
                    {roles_join}
                    WHERE {' OR '.join(where_parts)}
                    ORDER BY {order_by}
                    LIMIT :lim OFFSET :off
                """
                rows = (
                    (
                        await conn.execute(
                            sa_text(sql_txt),
                            {
                                "q": str(q or ""),
                                "qp": qp,
                                "lim": int(limit),
                                "off": int(offset),
                            },
                        )
                    )
                    .mappings()
                    .all()
                )

            items: list[dict[str, Any]] = []
            for row in rows:
                roles_list = row.get("roles") or []
                roles = [_normalise_role(x) for x in roles_list]
                status_value = "banned" if bool(row.get("is_banned")) else "active"
                notes_count = int(row.get("notes_count") or 0)
                items.append(
                    {
                        "id": str(row["id"]),
                        "username": row.get("username")
                        or row.get("email")
                        or str(row["id"]),
                        "email": row.get("email"),
                        "roles": roles,
                        "status": status_value,
                        "complaints_count": 0,
                        "notes_count": notes_count,
                        "sanction_count": 0,
                    }
                )

            return UseCaseResult(
                payload={
                    "items": items,
                    "next_cursor": (
                        str(offset + len(items)) if len(items) == int(limit) else None
                    ),
                }
            )
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning("/api/moderation/users DB path failed: %s", exc)

    service_result = await service_list_users(
        service,
        status=status,
        role=role,
        registered_from=registered_from,
        registered_to=registered_to,
        q=q,
        limit=limit,
        cursor=cursor,
    )
    items = [
        item.model_dump() if hasattr(item, "model_dump") else dict(item)
        for item in service_result.get("items", [])
    ]
    return UseCaseResult(
        payload={
            "items": items,
            "next_cursor": service_result.get("next_cursor"),
        }
    )


async def get_user(service, settings, user_id: str) -> UseCaseResult:
    engine = _build_engine(settings, suffix="detail")
    if engine is not None:
        try:
            async with engine.begin() as conn:
                have_user_roles = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_roles' LIMIT 1
                                """
                            )
                        )
                    ).first()
                )
                have_notes_table = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'moderator_user_notes' LIMIT 1
                                """
                            )
                        )
                    ).first()
                )
                if have_user_roles:
                    sql = sa_text(
                        """
                        SELECT u.id::text AS id,
                               COALESCE(u.username, u.display_name, u.email) AS username,
                               u.email,
                               COALESCE(ur.roles, ARRAY[]::text[]) AS roles
                        FROM users u
                        LEFT JOIN (
                          SELECT user_id, array_agg(role::text ORDER BY role) AS roles
                          FROM user_roles GROUP BY user_id
                        ) ur ON ur.user_id = u.id
                        WHERE u.id::text = :id
                        LIMIT 1
                        """
                    )
                else:
                    sql = sa_text(
                        """
                        SELECT u.id::text AS id,
                               COALESCE(u.username, u.display_name, u.email) AS username,
                               u.email,
                               ARRAY[COALESCE(u.role::text,'user')] AS roles
                        FROM users u
                        WHERE u.id::text = :id
                        LIMIT 1
                        """
                    )
                row = (await conn.execute(sql, {"id": str(user_id)})).mappings().first()
                if not row:
                    raise UserNotFoundError()
                if have_notes_table:
                    notes_rows = (
                        (
                            await conn.execute(
                                sa_text(
                                    """
                                    SELECT id::text AS id,
                                           text,
                                           author_id,
                                           author_name,
                                           pinned,
                                           created_at,
                                           meta
                                    FROM moderator_user_notes
                                    WHERE user_id = cast(:id as uuid)
                                    ORDER BY pinned DESC, created_at DESC, id DESC
                                    """
                                ),
                                {"id": str(row["id"])},
                            )
                        )
                        .mappings()
                        .all()
                    )
                else:
                    notes_rows = []

            notes = [ModeratorNoteDTO(**_note_row_to_dict(note)) for note in notes_rows]
            roles = [_normalise_role(x) for x in (row.get("roles") or [])]
            notes_count = len(notes)
            payload: dict[str, Any] = {
                "id": str(row["id"]),
                "username": str(row.get("username") or row.get("email") or row["id"]),
                "email": row.get("email") or None,
                "roles": roles,
                "status": "active",
                "registered_at": None,
                "last_seen_at": None,
                "complaints_count": 0,
                "notes_count": notes_count,
                "sanction_count": 0,
                "active_sanctions": [],
                "last_sanction": None,
                "meta": {},
                "sanctions": [],
                "reports": [],
                "tickets": [],
                "notes": [note.model_dump() for note in notes],
            }
            return UseCaseResult(payload=payload)
        except UserNotFoundError:
            raise
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning("moderation users: failed to fetch detail from DB: %s", exc)

    try:
        dto = await service_get_user(service, user_id)
    except KeyError as exc:
        raise UserNotFoundError() from exc
    payload = dto.model_dump() if hasattr(dto, "model_dump") else dict(dto)
    return UseCaseResult(payload=payload)


async def update_roles_use_case(
    service,
    settings,
    user_id: str,
    body: Mapping[str, Any],
) -> UseCaseResult:
    add = [str(r).strip().lower() for r in body.get("add", []) if r is not None]
    remove = [str(r).strip().lower() for r in body.get("remove", []) if r is not None]
    valid: set[str] = {"user", "support", "moderator", "admin"}
    add = [r for r in add if r in valid]
    remove = [r for r in remove if r in valid]

    engine = _build_engine(settings, suffix="roles")
    if engine is None:
        raise ModerationUserError(code="roles_update_failed", status_code=500)

    try:
        async with engine.begin() as conn:
            exists = (
                await conn.execute(
                    sa_text("SELECT 1 FROM users WHERE id = cast(:id as uuid) LIMIT 1"),
                    {"id": str(user_id)},
                )
            ).first()
            if not exists:
                raise UserNotFoundError()

            have_user_roles = bool(
                (
                    await conn.execute(
                        sa_text(
                            "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_roles' LIMIT 1"
                        )
                    )
                ).first()
            )
            has_role_col = bool(
                (
                    await conn.execute(
                        sa_text(
                            "SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'users' AND column_name = 'role' LIMIT 1"
                        )
                    )
                ).first()
            )

            if have_user_roles:
                for r in add:
                    await conn.execute(
                        sa_text(
                            "INSERT INTO user_roles (user_id, role) VALUES (cast(:id as uuid), CAST(:r AS user_role)) ON CONFLICT DO NOTHING"
                        ),
                        {"id": str(user_id), "r": r},
                    )
                for r in remove:
                    await conn.execute(
                        sa_text(
                            "DELETE FROM user_roles WHERE user_id = cast(:id as uuid) AND role = CAST(:r AS user_role)"
                        ),
                        {"id": str(user_id), "r": r},
                    )
                rows = (
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT role::text AS role FROM user_roles WHERE user_id = cast(:id as uuid) ORDER BY role"
                            ),
                            {"id": str(user_id)},
                        )
                    )
                    .mappings()
                    .all()
                )
                roles = [_normalise_role(row["role"]) for row in rows]
            else:
                current_row = (
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT role::text AS role FROM users WHERE id = cast(:id as uuid)"
                            ),
                            {"id": str(user_id)},
                        )
                    )
                    .mappings()
                    .first()
                    if has_role_col
                    else None
                )
                current = (
                    {str(current_row["role"]).lower()} if current_row else {"user"}
                )
                current -= set(remove)
                current |= set(add)
                chosen = sorted(current)
                await conn.execute(
                    sa_text(
                        "UPDATE users SET role = CAST(:role AS user_role) WHERE id = cast(:id as uuid)"
                    ),
                    {"role": chosen[0] if chosen else "user", "id": str(user_id)},
                )
                roles = [_normalise_role(chosen[0] if chosen else "user")]

        try:
            await service.update_roles(user_id, add=add, remove=remove)
        except KeyError:
            logger.debug("moderation users: service cache missing %s", user_id)
        except Exception as exc:
            logger.debug(
                "moderation users: unable to sync service roles for %s: %s",
                user_id,
                exc,
            )

        return UseCaseResult(
            payload={
                "user_id": user_id,
                "roles": roles,
            }
        )
    except UserNotFoundError:
        raise
    except (SQLAlchemyError, RuntimeError, ValueError, TypeError) as exc:
        raise ModerationUserError(
            code="roles_update_failed",
            status_code=400,
            message=f"roles_update_failed: {exc}",
        ) from exc


async def issue_sanction(
    service,
    settings,
    notifications,
    user_id: str,
    body: Mapping[str, Any],
    *,
    idempotency_key: str | None = None,
) -> UseCaseResult:
    # Bootstrap user information from SQL for service cache
    engine_bootstrap = _build_engine(settings, suffix="sanction-bootstrap")
    if engine_bootstrap is not None:
        try:
            async with engine_bootstrap.begin() as conn:
                row = (
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT id::text AS id, COALESCE(username, display_name, email) AS username, email FROM users WHERE id = cast(:id as uuid)"
                            ),
                            {"id": str(user_id)},
                        )
                    )
                    .mappings()
                    .first()
                )
                if not row:
                    raise UserNotFoundError()
                await service.ensure_user_stub(
                    user_id=str(row["id"]),
                    username=str(row.get("username") or row.get("email") or row["id"]),
                    email=row.get("email"),
                )
        except UserNotFoundError:
            raise
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning(
                "moderation users: failed to bootstrap user %s: %s", user_id, exc
            )

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

    warnings_count = 0
    auto_ban_created = False
    engine_store = _build_engine(settings, suffix="sanction-store")
    if engine_store is not None:
        try:
            async with engine_store.begin() as conn:
                exists_tbl = (
                    await conn.execute(
                        sa_text(
                            "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_sanctions' LIMIT 1"
                        )
                    )
                ).first()
                if exists_tbl:
                    await conn.execute(
                        sa_text(
                            """
                            INSERT INTO user_sanctions(
                              user_id, type, status, reason, issued_by, issued_at, starts_at, ends_at, meta
                            ) VALUES (
                              cast(:uid as uuid), :type, :status, :reason, :issued_by, now(), now(), :ends_at, :meta
                            )
                            """
                        ),
                        {
                            "uid": user_id,
                            "type": sanction.type.value,
                            "status": sanction.status.value,
                            "reason": sanction.reason,
                            "issued_by": actor_id or "system",
                            "ends_at": body.get("ends_at")
                            or body.get("expires_at")
                            or None,
                            "meta": json.dumps(
                                (
                                    sanction.model_dump().get("meta")
                                    if hasattr(sanction, "model_dump")
                                    else {}
                                ),
                                ensure_ascii=False,
                            ),
                        },
                    )
                    if sanction.type.value == "warning":
                        cnt_row = (
                            (
                                await conn.execute(
                                    sa_text(
                                        """
                                        SELECT count(*) AS c
                                        FROM user_sanctions
                                        WHERE user_id = cast(:uid as uuid) AND type = 'warning' AND status = 'active'
                                          AND issued_at >= now() - interval '10 days'
                                        """
                                    ),
                                    {"uid": user_id},
                                )
                            )
                            .mappings()
                            .first()
                        )
                        warnings_count = int(cnt_row["c"]) if cnt_row else 0
                        if warnings_count >= 3:
                            await conn.execute(
                                sa_text(
                                    """
                                    INSERT INTO user_sanctions(user_id, type, status, reason, issued_by, issued_at, starts_at, ends_at, meta)
                                    VALUES (cast(:uid as uuid), 'ban', 'active', :reason, :issued_by, now(), now(), NULL, :meta)
                                    """
                                ),
                                {
                                    "uid": user_id,
                                    "reason": f"auto_ban_three_warnings ({warnings_count}/3)",
                                    "issued_by": actor_id or "system",
                                    "meta": json.dumps(
                                        {
                                            "source": "auto_ban",
                                            "window_days": 10,
                                            "warnings_count": warnings_count,
                                        },
                                        ensure_ascii=False,
                                    ),
                                },
                            )
                            auto_ban_created = True
                    if not auto_ban_created:
                        auto_ban_created = bool(
                            (
                                await conn.execute(
                                    sa_text(
                                        "SELECT 1 FROM user_sanctions WHERE user_id = cast(:id as uuid) AND type = 'ban' AND status = 'active' AND starts_at <= now() AND (ends_at IS NULL OR ends_at > now()) LIMIT 1"
                                    ),
                                    {"id": user_id},
                                )
                            ).first()
                        )
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning(
                "moderation users: failed to persist sanction for %s: %s", user_id, exc
            )

    if notifications is not None:
        try:
            notify = notifications
            t = sanction.type.value
            if t == "warning":
                await notify.create_notification(
                    user_id=user_id,
                    title="Warning",
                    message=str(sanction.reason or "You have received a warning"),
                    type_="warning",
                )
                if auto_ban_created:
                    await notify.create_notification(
                        user_id=user_id,
                        title="Account banned",
                        message="You have been banned due to multiple warnings.",
                        type_="ban",
                    )
            elif t == "ban":
                await notify.create_notification(
                    user_id=user_id,
                    title="Account banned",
                    message=str(sanction.reason or "Your account has been banned"),
                    type_="ban",
                )
        except (AttributeError, RuntimeError, TypeError) as exc:
            logger.debug(
                "moderation users: notification dispatch failed for %s: %s",
                user_id,
                exc,
            )

    payload = (
        sanction.model_dump() if hasattr(sanction, "model_dump") else dict(sanction)
    )
    payload.setdefault("meta", {})
    payload["meta"].setdefault("warnings_count", warnings_count)
    return UseCaseResult(payload=payload)


async def update_sanction(
    service,
    user_id: str,
    sanction_id: str,
    body: Mapping[str, Any],
) -> UseCaseResult:
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
    return UseCaseResult(payload=payload)


async def add_note(
    service,
    settings,
    user_id: str,
    body: Mapping[str, Any],
) -> UseCaseResult:
    text_value = str(body.get("text") or "").strip()
    if not text_value:
        raise ModerationUserError(code="text_required", status_code=400)
    pinned = bool(body.get("pinned") or False)
    raw_meta = body.get("meta")
    meta = dict(raw_meta) if isinstance(raw_meta, Mapping) else {}
    author_id = body.get("author_id")
    author_name = body.get("author_name")
    note_payload = {
        "text": text_value,
        "author_id": author_id,
        "author_name": author_name,
        "pinned": pinned,
        "meta": meta,
    }
    sql_meta = json.dumps(meta, ensure_ascii=False)

    engine = _build_engine(settings, suffix="notes")
    if engine is not None:
        try:
            async with engine.begin() as conn:
                exists = (
                    await conn.execute(
                        sa_text(
                            "SELECT 1 FROM users WHERE id = cast(:id as uuid) LIMIT 1"
                        ),
                        {"id": str(user_id)},
                    )
                ).scalar()
                if not exists:
                    raise UserNotFoundError()
                have_notes_table = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1 FROM information_schema.tables
                                WHERE table_schema = current_schema() AND table_name = 'moderator_user_notes'
                                LIMIT 1
                                """
                            )
                        )
                    ).first()
                )
                if not have_notes_table:
                    raise RuntimeError("moderator_user_notes_missing")
                note_row = (
                    (
                        await conn.execute(
                            sa_text(
                                """
                                INSERT INTO moderator_user_notes (
                                    user_id,
                                    text,
                                    author_id,
                                    author_name,
                                    pinned,
                                    meta
                                )
                                VALUES (
                                    cast(:uid as uuid),
                                    :text,
                                    :author_id,
                                    :author_name,
                                    :pinned,
                                    :meta
                                )
                                RETURNING id::text AS id,
                                          text,
                                          author_id,
                                          author_name,
                                          pinned,
                                          created_at,
                                          meta
                                """
                            ),
                            {
                                "uid": str(user_id),
                                "text": text_value,
                                "author_id": author_id,
                                "author_name": author_name,
                                "pinned": pinned,
                                "meta": sql_meta,
                            },
                        )
                    )
                    .mappings()
                    .first()
                )
            if not note_row:
                raise ModerationUserError(
                    code="note_not_created",
                    status_code=500,
                    message="note_not_created",
                )
            return UseCaseResult(payload=_note_row_to_dict(note_row))
        except UserNotFoundError:
            raise
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning(
                "moderation users: SQL note persist failed for %s: %s", user_id, exc
            )

    try:
        await service.ensure_user_stub(user_id=user_id, username=user_id, email=None)
    except Exception:
        pass
    try:
        note = await service.add_note(
            user_id,
            note_payload,
            actor_id=author_id,
            actor_name=author_name,
        )
    except KeyError as exc:
        raise UserNotFoundError() from exc
    payload = note.model_dump() if hasattr(note, "model_dump") else dict(note)
    return UseCaseResult(payload=payload)


__all__ = [
    "UseCaseResult",
    "add_note",
    "get_user",
    "issue_sanction",
    "list_users",
    "update_roles_use_case",
    "update_sanction",
]
