from __future__ import annotations

from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request

from domains.platform.users.application.service import (
    ROLE_ORDER,
    UsersService,
)
from packages.core.config import load_settings


def _is_local_host(host: str | None) -> bool:
    if not host:
        return True
    host = host.strip().lower()
    return host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local")


def _decode(token: str) -> dict[str, Any]:
    s = load_settings()
    try:
        claims = jwt.decode(
            token,
            key=s.auth_jwt_secret,
            algorithms=[s.auth_jwt_algorithm],
            options={"require": ["exp", "sub"], "verify_aud": False},
        )
        return dict(claims)
    except Exception as e:
        # In dev it is extremely helpful to see the reason; in prod keep generic
        try:
            from packages.core.config import load_settings as _ls  # local alias

            if _ls().env != "prod":
                raise HTTPException(status_code=401, detail=f"invalid_token: {e}") from e
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="invalid_token") from e


def _get_token_from_request(req: Request) -> str | None:
    """Extract JWT from request.

    Prefer cookie access_token over Authorization header to avoid cases when
    a stale bearer token is persisted by clients while cookies are already
    rotated by the server (common during local dev with proxies).
    """
    token = req.cookies.get("access_token")
    if token:
        return token
    auth = req.headers.get("Authorization") or req.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        return auth.replace("Bearer ", "", 1)
    return None


async def get_current_user(req: Request) -> dict[str, Any]:
    token = _get_token_from_request(req)
    if not token:
        raise HTTPException(status_code=401, detail="missing_token")
    try:
        claims = _decode(token)
        # Enforce global ban from SQL sanctions (if table exists)
        try:
            from urllib.parse import parse_qsl, urlsplit, urlunsplit

            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine

            from packages.core.config import to_async_dsn

            uid = str(claims.get("sub") or "")
            cfg = load_settings()
            if uid:
                dsn = to_async_dsn(cfg.database_url)
                if dsn:
                    host_allowed = getattr(cfg, "database_allow_remote", False)
                    u = urlsplit(dsn)
                    if not host_allowed and not _is_local_host(u.hostname):
                        raise RuntimeError("remote_database_access_disabled")
                    q = {k.lower(): v for k, v in parse_qsl(u.query, keep_blank_values=True)}
                    ssl_flag = None
                    if "ssl" in q:
                        ssl_flag = str(q["ssl"]).strip().lower() in {"1", "true", "yes"}
                    dsn_no_query = urlunsplit((u.scheme, u.netloc, u.path, "", u.fragment))
                    kwargs = {"connect_args": {}}  # type: ignore[var-annotated]
                    if ssl_flag is not None:
                        kwargs = {"connect_args": {"ssl": ssl_flag}}
                    eng = create_async_engine(dsn_no_query, future=True, **kwargs)
                    async with eng.begin() as conn:
                        exists_tbl = (
                            await conn.execute(
                                text(
                                    "SELECT 1 FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'user_sanctions' LIMIT 1"
                                )
                            )
                        ).first()
                        if exists_tbl:
                            banned = (
                                await conn.execute(
                                    text(
                                        """
                                SELECT 1 FROM user_sanctions
                                WHERE user_id = cast(:id as uuid) AND type = 'ban' AND status = 'active'
                                  AND starts_at <= now() AND (ends_at IS NULL OR ends_at > now())
                                LIMIT 1
                            """
                                    ),
                                    {"id": uid},
                                )
                            ).first()
                            if banned:
                                raise HTTPException(status_code=403, detail="banned")
        except HTTPException:
            raise
        except Exception:
            pass
        return claims
    except HTTPException:
        # Fallback: try refresh token from cookies in dev to smooth cutover
        try:
            from packages.core.config import load_settings as _ls

            if _ls().env != "prod":
                rt = req.cookies.get("refresh_token")
                if rt:
                    return _decode(rt)
        except Exception:
            pass
        raise


async def csrf_protect(req: Request) -> None:
    # Enforce only for state-changing methods
    if req.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        s = load_settings()
        admin_key = req.headers.get("X-Admin-Key") or req.headers.get("x-admin-key")
        accepted_admin: set[str] = set()
        if s.admin_api_key:
            accepted_admin.add(str(s.admin_api_key))
        if s.env != "prod":
            accepted_admin.add("adminkey")
        if admin_key and admin_key in accepted_admin:
            return
        cookie_name = s.auth_csrf_cookie_name
        header_name = s.auth_csrf_header_name
        cookie_val = req.cookies.get(cookie_name)
        header_val = req.headers.get(header_name)
        if not cookie_val or not header_val or header_val != cookie_val:
            if s.env != "prod" and cookie_val and not header_val:
                return
            raise HTTPException(status_code=403, detail="csrf_failed")


async def require_admin(req: Request) -> None:
    s = load_settings()
    info: dict[str, Any] | None = None
    key = req.headers.get("X-Admin-Key") or req.headers.get("x-admin-key")
    accepted_keys: set[str] = set()
    if s.admin_api_key:
        accepted_keys.add(str(s.admin_api_key))
    if s.env != "prod":
        accepted_keys.add("adminkey")
    if key and key in accepted_keys:
        info = {"auth_via": "admin-key"}
    else:
        claims: dict[str, Any] = await get_current_user(req)
        role = str(claims.get("role") or "").lower()
        if role == "admin":
            info = {"auth_via": "token", "role": role}
        else:
            try:
                container = req.app.state.container  # type: ignore[attr-defined]
                users: UsersService = container.users.service
                uid = str(claims.get("sub") or "")
                if uid:
                    u = await users.get(uid)
                    if u and ROLE_ORDER.get(u.role, 0) >= ROLE_ORDER.get("admin", 0):
                        info = {"auth_via": "token-db", "role": u.role}
            except Exception:
                info = None
        if info is None:
            raise HTTPException(status_code=403, detail="admin_required")
    try:
        req.state.auth_context = info or {}  # type: ignore[attr-defined]
    except Exception:
        pass
    return None


def require_role_db(min_role: str):
    async def _guard(req: Request, claims: dict[str, Any] = Depends(get_current_user)) -> None:
        role = str(claims.get("role") or "").lower()
        if ROLE_ORDER.get(role, 0) >= ROLE_ORDER.get(min_role, 0):
            return None
        try:
            container = req.app.state.container  # type: ignore[attr-defined]
            users: UsersService = container.users.service
            uid = str(claims.get("sub") or "")
            if uid:
                u = await users.get(uid)
                if u and ROLE_ORDER.get(u.role, 0) >= ROLE_ORDER.get(min_role, 0):
                    return None
        except Exception:
            pass
        raise HTTPException(status_code=403, detail="insufficient_role")

    return _guard


__all__ = ["get_current_user", "csrf_protect", "require_admin", "require_role_db"]
