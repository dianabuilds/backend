from __future__ import annotations

from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request

from domains.platform.users.application.service import (
    ROLE_ORDER,
    UsersService,
)
from packages.core.config import load_settings


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
        raise HTTPException(status_code=401, detail="invalid_token") from e


def _get_token_from_request(req: Request) -> str | None:
    # Prefer cookie; fall back to Authorization header
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
    return _decode(token)


async def csrf_protect(req: Request) -> None:
    # Enforce only for state-changing methods
    if req.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        s = load_settings()
        cookie_name = s.auth_csrf_cookie_name
        header_name = s.auth_csrf_header_name
        cookie_val = req.cookies.get(cookie_name)
        header_val = req.headers.get(header_name)
        if not cookie_val or not header_val or header_val != cookie_val:
            raise HTTPException(status_code=403, detail="csrf_failed")


async def require_admin(
    req: Request, claims: dict[str, Any] = Depends(get_current_user)
) -> None:
    s = load_settings()
    # Header key wins if provided
    key = req.headers.get("X-Admin-Key") or req.headers.get("x-admin-key")
    if s.admin_api_key and key and key == s.admin_api_key:
        return None
    # Else check role claim on JWT
    role = str(claims.get("role") or "").lower()
    if role == "admin":
        return None
    # Optional DB check for robustness
    try:
        container = req.app.state.container  # type: ignore[attr-defined]
        users: UsersService = container.users.service
        uid = str(claims.get("sub") or "")
        if uid:
            u = await users.get(uid)
            if u and ROLE_ORDER.get(u.role, 0) >= ROLE_ORDER.get("admin", 0):
                return None
    except Exception:
        pass
    raise HTTPException(status_code=403, detail="admin_required")


def require_role_db(min_role: str):
    async def _guard(
        req: Request, claims: dict[str, Any] = Depends(get_current_user)
    ) -> None:
        # Claim short‑path
        role = str(claims.get("role") or "").lower()
        if ROLE_ORDER.get(role, 0) >= ROLE_ORDER.get(min_role, 0):
            return None
        # Fallback to DB role if available
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


__all__ = ["get_current_user", "csrf_protect", "require_admin"]
