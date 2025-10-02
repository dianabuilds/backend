import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

from ..dtos import ModeratorNoteDTO, SanctionDTO, UserDetail
from ..rbac import require_scopes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["moderation-users"])


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


@router.get("", dependencies=[Depends(require_scopes("moderation:users:read"))])
async def list_users(
    status: str | None = None,
    role: str | None = None,
    registered_from: str | None = None,
    registered_to: str | None = None,
    q: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    # Prefer real DB data; if Р‘Р” РЅРµРґРѕСЃС‚СѓРїРЅР° вЂ” РІРµСЂРЅСѓС‚СЊ РїСѓСЃС‚РѕР№ СЃРїРёСЃРѕРє
    try:
        dsn = to_async_dsn(container.settings.database_url)
        if not dsn:
            return {"items": [], "next_cursor": None}

        eng = get_async_engine("moderation-users-list", url=dsn, future=True)

        qp = f"%{(q or '').strip()}%"
        try:
            offset = int(cursor or 0)
        except (TypeError, ValueError) as exc:
            logger.debug("moderation users: invalid cursor %r: %s", cursor, exc)
            offset = 0
        async with eng.begin() as conn:
            # Detect if user_roles table exists
            have_user_roles = bool(
                (
                    await conn.execute(
                        text(
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
                        text(
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

            # Detect user columns
            cols = (
                (
                    await conn.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'users'"
                        )
                    )
                )
                .scalars()
                .all()
            )
            cols_set = {str(c) for c in cols}

            name_expr_parts = []
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
            like_exprs = []
            if "username" in cols_set:
                like_exprs.append("lower(COALESCE(u.username, '')) LIKE lower(:qp)")
            if "display_name" in cols_set:
                like_exprs.append("lower(COALESCE(u.display_name, '')) LIKE lower(:qp)")
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

            # Check active ban (SQL sanctions)
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
            sql = text(sql_txt)
            rows = (
                (
                    await conn.execute(
                        sql,
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

        def _cap(s: str) -> str:
            try:
                return s[:1].upper() + s[1:].lower()
            except (AttributeError, TypeError) as exc:
                logger.debug("moderation users: cannot normalise role %r: %s", s, exc)
                return str(s)

        items = []
        for r in rows:
            roles_list = r.get("roles") or []
            roles = [_cap(str(x)) for x in roles_list]
            status = "banned" if bool(r.get("is_banned")) else "active"
            notes_count = int(r.get("notes_count") or 0)
            items.append(
                {
                    "id": str(r["id"]),
                    "username": (r.get("username") or r.get("email") or str(r["id"])),
                    "email": r.get("email"),
                    "roles": roles,
                    "status": status,
                    "complaints_count": 0,
                    "notes_count": notes_count,
                    "sanction_count": 0,
                }
            )
        return {
            "items": items,
            "next_cursor": (
                str(offset + len(items)) if len(items) == int(limit) else None
            ),
        }
    except (SQLAlchemyError, RuntimeError, ValueError, TypeError, ImportError) as exc:
        logger.warning("/api/moderation/users DB path failed: %s", exc)
        # Fallback for common schema (id, email, username, display_name, created_at)
        try:
            dsn = to_async_dsn(container.settings.database_url)
            if not dsn:
                return {"items": [], "next_cursor": None}

            eng = get_async_engine(
                "moderation-users-list-fallback", url=dsn, future=True
            )

            qp = f"%{(q or '').strip()}%"
            try:
                offset = int(cursor or 0)
            except (TypeError, ValueError) as exc:
                logger.debug("moderation users: invalid cursor %r: %s", cursor, exc)
                offset = 0

            async with eng.begin() as conn:
                have_notes_table_fb = bool(
                    (
                        await conn.execute(
                            text(
                                """
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = current_schema() AND table_name = 'moderator_user_notes'
                        LIMIT 1
                                """
                            )
                        )
                    ).first()
                )
                notes_select_fb = (
                    "(SELECT COUNT(*) FROM moderator_user_notes mn WHERE mn.user_id = u.id) AS notes_count"
                    if have_notes_table_fb
                    else "0 AS notes_count"
                )
                sql = text(
                    f"""
                    SELECT u.id::text AS id,
                           COALESCE(u.username, u.display_name, u.email) AS username,
                           u.email,
                           'user' AS role,
                           {notes_select_fb}
                    FROM users u
                    WHERE (:q = '' OR lower(COALESCE(u.username, '')) LIKE lower(:qp)
                                   OR lower(COALESCE(u.display_name, '')) LIKE lower(:qp)
                                   OR lower(COALESCE(u.email, '')) LIKE lower(:qp))
                    ORDER BY u.created_at DESC NULLS LAST, u.id DESC
                    LIMIT :lim OFFSET :off
                    """
                )
                rows = (
                    (
                        await conn.execute(
                            sql,
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
            items = [
                {
                    "id": str(r["id"]),
                    "username": (r.get("username") or r.get("email") or str(r["id"])),
                    "email": r.get("email"),
                    "roles": [str(r.get("role") or "user").capitalize()],
                    "status": "active",
                    "complaints_count": 0,
                    "notes_count": int(r.get("notes_count") or 0),
                    "sanction_count": 0,
                }
                for r in rows
            ]
            return {
                "items": items,
                "next_cursor": (
                    str(offset + len(items)) if len(items) == int(limit) else None
                ),
            }
        except (
            SQLAlchemyError,
            RuntimeError,
            ValueError,
            TypeError,
            ImportError,
        ) as exc:
            logger.warning("/api/moderation/users fallback failed: %s", exc)
            return {"items": [], "next_cursor": None}


@router.get(
    "/{user_id}",
    response_model=UserDetail,
    dependencies=[Depends(require_scopes("moderation:users:read"))],
)
async def get_user(user_id: str, container=Depends(get_container)) -> UserDetail:
    # Try DB first: build minimal UserDetail; fallback -> 404
    try:
        dsn = to_async_dsn(container.settings.database_url)
        if not dsn:
            raise KeyError("no_dsn")

        eng = get_async_engine("moderation-users-detail", url=dsn, future=True)

        async with eng.begin() as conn:
            # detect user_roles
            have_user_roles = bool(
                (
                    await conn.execute(
                        text(
                            "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_roles' LIMIT 1"
                        )
                    )
                ).first()
            )
            have_notes_table = bool(
                (
                    await conn.execute(
                        text(
                            "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'moderator_user_notes' LIMIT 1"
                        )
                    )
                ).first()
            )
            if have_user_roles:
                sql = text(
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
                sql = text(
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
                raise KeyError(user_id)
            if have_notes_table:
                notes_rows = (
                    (
                        await conn.execute(
                            text(
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
        roles = [
            (str(x)[:1].upper() + str(x)[1:].lower()) for x in (row.get("roles") or [])
        ]
        notes_count = len(notes)
        return UserDetail(
            id=str(row["id"]),
            username=str(row.get("username") or row.get("email") or row["id"]),
            email=(row.get("email") or None),
            roles=roles,
            status="active",
            registered_at=None,
            last_seen_at=None,
            complaints_count=0,
            notes_count=notes_count,
            sanction_count=0,
            active_sanctions=[],
            last_sanction=None,
            meta={},
            sanctions=[],
            reports=[],
            tickets=[],
            notes=notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="user_not_found") from exc


@router.post(
    "/{user_id}/roles",
    dependencies=[Depends(require_scopes("moderation:users:roles:write"))],
)
async def update_roles(
    user_id: str, body: dict[str, list[str]], container=Depends(get_container)
) -> dict[str, Any]:
    """Update roles in SQL if available (user_roles M2M preferred), otherwise fallback to users.role.

    Body format:
      { "add": ["Admin"], "remove": ["User"] }
    Roles are case-insensitive; valid set: user, support, moderator, admin.
    """
    add = [str(r).strip().lower() for r in body.get("add", []) if r is not None]
    remove = [str(r).strip().lower() for r in body.get("remove", []) if r is not None]
    valid: set[str] = {"user", "support", "moderator", "admin"}
    add = [r for r in add if r in valid]
    remove = [r for r in remove if r in valid]

    # Connect to DB
    try:
        dsn = to_async_dsn(container.settings.database_url)
        if not dsn:
            raise KeyError("no_dsn")

        eng = get_async_engine("moderation-users-roles", url=dsn, future=True)

        async with eng.begin() as conn:
            # ensure user exists
            exists = (
                await conn.execute(
                    text("SELECT 1 FROM users WHERE id = cast(:id as uuid) LIMIT 1"),
                    {"id": str(user_id)},
                )
            ).first()
            if not exists:
                raise KeyError(user_id)

            # detect user_roles and users.role columns
            have_user_roles = bool(
                (
                    await conn.execute(
                        text(
                            "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_roles' LIMIT 1"
                        )
                    )
                ).first()
            )
            has_role_col = bool(
                (
                    await conn.execute(
                        text(
                            "SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'users' AND column_name = 'role' LIMIT 1"
                        )
                    )
                ).first()
            )

            if have_user_roles:
                # apply add/remove to M2M
                for r in add:
                    await conn.execute(
                        text(
                            "INSERT INTO user_roles (user_id, role) VALUES (cast(:id as uuid), CAST(:r AS user_role)) ON CONFLICT DO NOTHING"
                        ),
                        {"id": str(user_id), "r": r},
                    )
                for r in remove:
                    await conn.execute(
                        text(
                            "DELETE FROM user_roles WHERE user_id = cast(:id as uuid) AND role = CAST(:r AS user_role)"
                        ),
                        {"id": str(user_id), "r": r},
                    )
                # fetch roles
                rows = (
                    (
                        await conn.execute(
                            text(
                                "SELECT role::text AS role FROM user_roles WHERE user_id = cast(:id as uuid) ORDER BY role"
                            ),
                            {"id": str(user_id)},
                        )
                    )
                    .mappings()
                    .all()
                )
                roles = [str(r["role"]) for r in rows]
            else:
                # single role column fallback
                current_row = (
                    (
                        await conn.execute(
                            text(
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
                    str(current_row["role"])
                    if current_row and current_row.get("role")
                    else "user"
                )
                target = current
                if add:
                    target = add[0]
                elif remove and current in remove:
                    target = "user"
                if has_role_col:
                    await conn.execute(
                        text(
                            "UPDATE users SET role = CAST(:r AS user_role) WHERE id = cast(:id as uuid)"
                        ),
                        {"id": str(user_id), "r": target},
                    )
                roles = [target]

        # Normalize case for UI
        def _cap(s: str) -> str:
            try:
                return s[:1].upper() + s[1:].lower()
            except (AttributeError, TypeError) as exc:
                logger.debug("moderation users: cannot normalise role %r: %s", s, exc)
                return str(s)

        return {"user_id": user_id, "roles": [_cap(r) for r in roles]}

    except KeyError as exc:
        raise HTTPException(status_code=404, detail="user_not_found") from exc
    except (SQLAlchemyError, RuntimeError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400, detail=f"roles_update_failed: {exc}"
        ) from exc


@router.post(
    "/{user_id}/sanctions",
    response_model=SanctionDTO,
    dependencies=[Depends(require_scopes("moderation:users:sanctions:write"))],
)
async def issue_sanction(
    user_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
    idempotency_key: str | None = Header(
        default=None, convert_underscores=False, alias="Idempotency-Key"
    ),
) -> SanctionDTO:
    svc = container.platform_moderation.service
    try:
        # Ensure the in-memory service knows about this user (load minimal stub from DB)
        try:
            dsn = to_async_dsn(container.settings.database_url)
            if dsn:
                eng = get_async_engine(
                    "moderation-users-sanction-bootstrap", url=dsn, future=True
                )
                async with eng.begin() as conn:
                    row = (
                        (
                            await conn.execute(
                                text(
                                    "SELECT id::text AS id, COALESCE(username, display_name, email) AS username, email FROM users WHERE id = cast(:id as uuid)"
                                ),
                                {"id": str(user_id)},
                            )
                        )
                        .mappings()
                        .first()
                    )
                    if not row:
                        raise KeyError(user_id)
                    await svc.ensure_user_stub(
                        user_id=str(row["id"]),
                        username=str(
                            row.get("username") or row.get("email") or row["id"]
                        ),
                        email=row.get("email"),
                    )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="user_not_found") from exc
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

        actor_id = body.get("issued_by")
        sanction = await svc.issue_sanction(
            user_id,
            body,
            actor_id=actor_id,
            idempotency_key=idempotency_key,
        )
        # Persist sanction in SQL table user_sanctions (best-effort)
        try:
            dsn = to_async_dsn(container.settings.database_url)
            if dsn:
                eng = get_async_engine(
                    "moderation-users-sanction-store", url=dsn, future=True
                )
                async with eng.begin() as conn:
                    # ensure table exists
                    exists_tbl = (
                        await conn.execute(
                            text(
                                "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_sanctions' LIMIT 1"
                            )
                        )
                    ).first()
                    if exists_tbl:
                        await conn.execute(
                            text(
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
                                "issued_by": (actor_id or "system"),
                                "ends_at": body.get("ends_at")
                                or body.get("expires_at")
                                or None,
                                "meta": (
                                    sanction.model_dump().get("meta")
                                    if hasattr(sanction, "model_dump")
                                    else {}
                                ),
                            },
                        )
                        # SQL auto-ban for warnings (3 in 10 days)
                        if sanction.type.value == "warning":
                            cnt_row = (
                                (
                                    await conn.execute(
                                        text(
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
                            warn_count = int(cnt_row["c"]) if cnt_row else 0
                            if warn_count >= 3:
                                await conn.execute(
                                    text(
                                        """
                                        INSERT INTO user_sanctions(user_id, type, status, reason, issued_by, issued_at, starts_at, ends_at, meta)
                                        VALUES (cast(:uid as uuid), 'ban', 'active', :reason, :issued_by, now(), now(), NULL, :meta)
                                        """
                                    ),
                                    {
                                        "uid": user_id,
                                        "reason": f"auto_ban_three_warnings ({warn_count}/3)",
                                        "issued_by": (actor_id or "system"),
                                        "meta": {
                                            "source": "auto_ban",
                                            "window_days": 10,
                                            "warnings_count": warn_count,
                                        },
                                    },
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
        # Notifications: warning/ban
        try:
            notify = container.notifications.notify  # type: ignore[attr-defined]
            t = sanction.type.value
            if t == "warning":
                await notify.create_notification(
                    user_id=user_id,
                    title="Warning",
                    message=str(sanction.reason or "You have received a warning"),
                    type_="warning",
                )
                # Check recent warnings and notify about auto-ban if threshold reached
                try:
                    # if an auto-ban was created in SQL, reflect via notification
                    auto_ban = (
                        (
                            await conn.execute(
                                text(
                                    "SELECT 1 FROM user_sanctions WHERE user_id = cast(:id as uuid) AND type = 'ban' AND status = 'active' AND starts_at <= now() AND (ends_at IS NULL OR ends_at > now()) LIMIT 1"
                                ),
                                {"id": user_id},
                            )
                        ).first()
                        if "conn" in locals()
                        else None
                    )
                    if auto_ban:
                        await notify.create_notification(
                            user_id=user_id,
                            title="Account banned",
                            message="You have been banned due to multiple warnings.",
                            type_="ban",
                        )
                except (SQLAlchemyError, RuntimeError) as exc:
                    logger.debug(
                        "moderation users: unable to check auto-ban state for %s: %s",
                        user_id,
                        exc,
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
        return sanction
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="user_not_found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch(
    "/{user_id}/sanctions/{sanction_id}",
    response_model=SanctionDTO,
    dependencies=[Depends(require_scopes("moderation:users:sanctions:write"))],
)
async def update_sanction(
    user_id: str,
    sanction_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> SanctionDTO:
    svc = container.platform_moderation.service
    try:
        return await svc.update_sanction(
            user_id, sanction_id, body, actor_id=body.get("actor_id")
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="sanction_not_found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/{user_id}/notes",
    dependencies=[Depends(require_scopes("moderation:users:notes:write"))],
)
async def add_note(
    user_id: str, body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    text_value = str(body.get("text") or "").strip()
    if not text_value:
        raise HTTPException(status_code=400, detail="text_required")
    pinned = bool(body.get("pinned") or False)
    raw_meta = body.get("meta")
    meta = dict(raw_meta) if isinstance(raw_meta, dict) else {}
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
    try:
        dsn = to_async_dsn(container.settings.database_url)
        if not dsn:
            raise RuntimeError("no_dsn")
        eng = get_async_engine("moderation-users-notes", url=dsn, future=True)
        async with eng.begin() as conn:
            exists = (
                await conn.execute(
                    text("SELECT 1 FROM users WHERE id = cast(:id as uuid) LIMIT 1"),
                    {"id": str(user_id)},
                )
            ).scalar()
            if not exists:
                raise HTTPException(status_code=404, detail="user_not_found")
            have_notes_table = bool(
                (
                    await conn.execute(
                        text(
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
                        text(
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
            raise HTTPException(status_code=500, detail="note_not_created")
        return _note_row_to_dict(note_row)
    except HTTPException:
        raise
    except (SQLAlchemyError, RuntimeError, ValueError, TypeError, ImportError) as exc:
        logger.warning(
            "moderation users: SQL note persist failed for %s: %s", user_id, exc
        )
    svc = container.platform_moderation.service
    try:
        note = await svc.add_note(
            user_id,
            note_payload,
            actor_id=author_id,
            actor_name=author_name,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="user_not_found") from exc
    return note.model_dump()


__all__ = ["router"]
