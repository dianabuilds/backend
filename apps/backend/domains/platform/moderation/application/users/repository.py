from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.testing import is_test_mode

from .exceptions import ModerationUserError, UserNotFoundError

logger = logging.getLogger(__name__)


def _should_use_sql(settings: Any | None) -> bool:
    if settings is None:
        return False
    if is_test_mode(settings):
        return False
    return True


def _build_engine(settings: Any | None, *, suffix: str) -> AsyncEngine | None:
    if not _should_use_sql(settings):
        return None
    try:  # pragma: no cover - optional dependency
        from packages.core.config import to_async_dsn
        from packages.core.db import get_async_engine
    except ModuleNotFoundError:
        return None
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        logger.debug("moderation users repository: no database_url configured")
        return None
    try:
        dsn = to_async_dsn(database_url)
    except (TypeError, ValueError) as exc:  # pragma: no cover - config errors
        logger.debug("moderation users repository: invalid DSN: %s", exc)
        return None
    if not dsn:
        return None
    try:
        return get_async_engine(f"moderation-users-{suffix}", url=dsn, future=True)
    except (SQLAlchemyError, RuntimeError, ImportError) as exc:  # pragma: no cover
        logger.warning("moderation users repository: failed to create engine: %s", exc)
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
        logger.debug(
            "moderation users repository: cannot normalise role %r: %s", value, exc
        )
        return str(value)
    if not text:
        return "User"
    return text[:1].upper() + text[1:].lower()


class ModerationUsersRepository:
    """SQL helper for moderation users endpoints.

    The repository mirrors legacy SQL logic that previously lived in use-cases.
    Each call is lazy: an engine is created only when required and missing
    dependencies quietly fall back to in-memory service behaviour.
    """

    def __init__(self, settings: Any | None) -> None:
        self._settings = settings

    async def list_users(
        self,
        *,
        status: str | None = None,
        role: str | None = None,
        registered_from: str | None = None,
        registered_to: str | None = None,
        q: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any] | None:
        engine = _build_engine(self._settings, suffix="list")
        if engine is None:
            return None
        try:
            async with engine.begin() as conn:
                qp = f"%{(q or '').strip()}%"
                try:
                    offset = int(cursor or 0)
                except (TypeError, ValueError) as exc:
                    logger.debug("moderation users: invalid cursor %r: %s", cursor, exc)
                    offset = 0

                have_user_roles = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1
                                FROM information_schema.tables
                                WHERE table_schema = current_schema()
                                  AND table_name = 'user_roles'
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
                                SELECT 1
                                FROM information_schema.tables
                                WHERE table_schema = current_schema()
                                  AND table_name = 'moderator_user_notes'
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
                                "SELECT column_name FROM information_schema.columns "
                                "WHERE table_schema = current_schema() AND table_name = 'users'"
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
                    "AND s.status = 'active' AND s.starts_at <= now() "
                    "AND (s.ends_at IS NULL OR s.ends_at > now()))"
                )

                sql_lines = [
                    "SELECT u.id::text AS id,",
                    f"{name_expr} AS username,",
                    "u.email,",
                    f"{roles_select},",
                    f"{ban_exists} AS is_banned,",
                    f"{notes_select}",
                    "FROM users u",
                    roles_join,
                ]
                if where_parts:
                    sql_lines.append("WHERE " + " OR ".join(where_parts))
                sql_lines.append("ORDER BY " + order_by)
                sql_lines.append("LIMIT :lim OFFSET :off")
                sql_txt = "\n".join(sql_lines)

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
                        "registered_at": None,
                        "last_seen_at": None,
                        "complaints_count": 0,
                        "notes_count": notes_count,
                        "sanction_count": 0,
                        "active_sanctions": [],
                        "last_sanction": None,
                        "meta": {},
                    }
                )

            next_cursor = str(offset + len(items)) if len(items) == int(limit) else None
            return {"items": items, "next_cursor": next_cursor}
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning("/api/moderation/users DB path failed: %s", exc)
            return None

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        engine = _build_engine(self._settings, suffix="detail")
        if engine is None:
            return None
        try:
            async with engine.begin() as conn:
                have_user_roles = bool(
                    (
                        await conn.execute(
                            sa_text(
                                """
                                SELECT 1
                                FROM information_schema.tables
                                WHERE table_schema = current_schema()
                                  AND table_name = 'user_roles'
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
                                SELECT 1
                                FROM information_schema.tables
                                WHERE table_schema = current_schema()
                                  AND table_name = 'moderator_user_notes'
                                LIMIT 1
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

            roles = [_normalise_role(x) for x in (row.get("roles") or [])]
            notes = [_note_row_to_dict(note) for note in notes_rows]
            notes_count = len(notes)
            return {
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
                "notes": notes,
            }
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
            return None

    async def bootstrap_user_stub(self, user_id: str) -> dict[str, Any]:
        engine = _build_engine(self._settings, suffix="sanction-bootstrap")
        if engine is None:
            raise UserNotFoundError()
        try:
            async with engine.begin() as conn:
                row = (
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT id::text AS id, COALESCE(username, display_name, email) AS username, email "
                                "FROM users WHERE id = cast(:id as uuid)"
                            ),
                            {"id": str(user_id)},
                        )
                    )
                    .mappings()
                    .first()
                )
            if not row:
                raise UserNotFoundError()
            return {
                "id": str(row["id"]),
                "username": str(row.get("username") or row.get("email") or row["id"]),
                "email": row.get("email"),
            }
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
            raise UserNotFoundError() from exc

    async def persist_sanction(
        self,
        user_id: str,
        sanction_payload: Mapping[str, Any],
        *,
        actor_id: str | None,
        warnings_window_days: int = 10,
    ) -> tuple[int, bool]:
        engine = _build_engine(self._settings, suffix="sanction-store")
        if engine is None:
            return 0, False
        warnings_count = 0
        auto_ban_created = False
        try:
            async with engine.begin() as conn:
                exists_tbl = (
                    await conn.execute(
                        sa_text(
                            "SELECT 1 FROM information_schema.tables "
                            "WHERE table_schema = current_schema() "
                            "AND table_name = 'user_sanctions' LIMIT 1"
                        )
                    )
                ).first()
                if not exists_tbl:
                    return 0, False
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
                        "type": sanction_payload.get("type"),
                        "status": sanction_payload.get("status"),
                        "reason": sanction_payload.get("reason"),
                        "issued_by": actor_id or "system",
                        "ends_at": sanction_payload.get("ends_at")
                        or sanction_payload.get("expires_at"),
                        "meta": json.dumps(
                            sanction_payload.get("meta") or {}, ensure_ascii=False
                        ),
                    },
                )
                if sanction_payload.get("type") == "warning":
                    cnt_row = (
                        (
                            await conn.execute(
                                sa_text(
                                    """
                                    SELECT count(*) AS c
                                    FROM user_sanctions
                                    WHERE user_id = cast(:uid as uuid)
                                      AND type = 'warning'
                                      AND status = 'active'
                                      AND issued_at >= now() - interval '{warnings_window_days} days'
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
                                INSERT INTO user_sanctions(
                                    user_id, type, status, reason, issued_by, issued_at, starts_at, ends_at, meta
                                ) VALUES (
                                    cast(:uid as uuid), 'ban', 'active', :reason, :issued_by, now(), now(), NULL, :meta
                                )
                                """
                            ),
                            {
                                "uid": user_id,
                                "reason": f"auto_ban_three_warnings ({warnings_count}/3)",
                                "issued_by": actor_id or "system",
                                "meta": json.dumps(
                                    {
                                        "source": "auto_ban",
                                        "window_days": warnings_window_days,
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
                                    "SELECT 1 FROM user_sanctions WHERE user_id = cast(:id as uuid) "
                                    "AND type = 'ban' AND status = 'active' AND starts_at <= now() "
                                    "AND (ends_at IS NULL OR ends_at > now()) LIMIT 1"
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
        return warnings_count, auto_ban_created

    async def update_roles(
        self,
        user_id: str,
        add: Iterable[str],
        remove: Iterable[str],
    ) -> list[str]:
        engine = _build_engine(self._settings, suffix="roles")
        if engine is None:
            raise ModerationUserError(code="roles_update_failed", status_code=500)
        add = [str(r).strip().lower() for r in add if r is not None]
        remove = [str(r).strip().lower() for r in remove if r is not None]
        valid: set[str] = {"user", "support", "moderator", "admin"}
        add = [r for r in add if r in valid]
        remove = [r for r in remove if r in valid]
        try:
            async with engine.begin() as conn:
                exists = (
                    await conn.execute(
                        sa_text(
                            "SELECT 1 FROM users WHERE id = cast(:id as uuid) LIMIT 1"
                        ),
                        {"id": str(user_id)},
                    )
                ).first()
                if not exists:
                    raise UserNotFoundError()

                have_user_roles = bool(
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT 1 FROM information_schema.tables "
                                "WHERE table_schema = current_schema() AND table_name = 'user_roles' LIMIT 1"
                            )
                        )
                    ).first()
                )
                has_role_col = bool(
                    (
                        await conn.execute(
                            sa_text(
                                "SELECT 1 FROM information_schema.columns "
                                "WHERE table_schema = current_schema() AND table_name = 'users' "
                                "AND column_name = 'role' LIMIT 1"
                            )
                        )
                    ).first()
                )

                if have_user_roles:
                    for role in add:
                        await conn.execute(
                            sa_text(
                                "INSERT INTO user_roles (user_id, role) VALUES (cast(:id as uuid), CAST(:r AS user_role)) "
                                "ON CONFLICT DO NOTHING"
                            ),
                            {"id": str(user_id), "r": role},
                        )
                    for role in remove:
                        await conn.execute(
                            sa_text(
                                "DELETE FROM user_roles WHERE user_id = cast(:id as uuid) AND role = CAST(:r AS user_role)"
                            ),
                            {"id": str(user_id), "r": role},
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
            return roles
        except UserNotFoundError:
            raise
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
        ) as exc:
            raise ModerationUserError(
                code="roles_update_failed",
                status_code=400,
                message=f"roles_update_failed: {exc}",
            ) from exc

    async def add_note(
        self,
        user_id: str,
        *,
        text: str,
        author_id: str | None,
        author_name: str | None,
        pinned: bool,
        meta: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        engine = _build_engine(self._settings, suffix="notes")
        if engine is None:
            return None
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
                                ) VALUES (
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
                                "text": text,
                                "author_id": author_id,
                                "author_name": author_name,
                                "pinned": pinned,
                                "meta": json.dumps(dict(meta), ensure_ascii=False),
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
            return _note_row_to_dict(note_row)
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
            return None


def create_repository(settings: Any | None) -> ModerationUsersRepository:
    return ModerationUsersRepository(settings=settings)


__all__ = ["ModerationUsersRepository", "create_repository"]
