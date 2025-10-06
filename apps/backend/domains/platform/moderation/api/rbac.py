import logging
from collections.abc import Callable, Iterable
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from starlette.requests import Request

# Basic role names used across the system
ROLE_ADMIN = "Admin"
ROLE_MODERATOR = "Moderator"
ROLE_EDITOR = "Editor"
ROLE_USER = "User"


# Moderation scopes used by the routers
SCOPES = {
    "moderation:overview:read",
    "moderation:users:read",
    "moderation:users:roles:write",
    "moderation:users:sanctions:write",
    "moderation:users:notes:write",
    "moderation:content:read",
    "moderation:content:decide:write",
    "moderation:content:edit:write",
    "moderation:reports:read",
    "moderation:reports:resolve:write",
    "moderation:reports:validate:write",
    "moderation:tickets:read",
    "moderation:tickets:comment:write",
    "moderation:tickets:close:write",
    "moderation:appeals:read",
    "moderation:appeals:decide:write",
    "moderation:ai-rules:read",
    "moderation:ai-rules:write",
}


# Simple role>scopes mapping. Adjust if your auth system differs.
ROLE_TO_SCOPES = {
    ROLE_ADMIN: {
        *SCOPES,
    },
    ROLE_MODERATOR: {
        "moderation:overview:read",
        "moderation:users:read",
        "moderation:users:sanctions:write",
        "moderation:users:notes:write",
        "moderation:content:read",
        "moderation:content:decide:write",
        "moderation:reports:read",
        "moderation:reports:resolve:write",
        "moderation:tickets:read",
        "moderation:tickets:comment:write",
        "moderation:tickets:close:write",
        "moderation:appeals:read",
        "moderation:appeals:decide:write",
    },
    ROLE_EDITOR: {
        "moderation:overview:read",
        "moderation:users:read",  # read-only; write limited to notes
        "moderation:users:notes:write",
        "moderation:content:read",
        "moderation:content:edit:write",
        "moderation:reports:read",
        "moderation:reports:validate:write",
        "moderation:tickets:read",
        "moderation:tickets:comment:write",
        "moderation:appeals:read",
    },
    ROLE_USER: set(),
}


logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _load_settings_safe() -> Any | None:
    try:
        from packages.core.config import load_settings  # type: ignore
    except ImportError as exc:
        logger.warning("Moderation RBAC cannot import settings: %s", exc)
        return None
    try:
        return load_settings()
    except (ValidationError, RuntimeError, OSError) as exc:
        logger.warning("Moderation RBAC cannot load settings: %s", exc)
        return None


def _normalize_roles(candidate: Any) -> list[str]:
    if candidate is None:
        return []
    try:
        return [str(role) for role in candidate]
    except TypeError as exc:
        logger.debug("Role container %r is not iterable: %s", candidate, exc)
        return []
    except AttributeError as exc:
        logger.debug("Role container %r missing attribute access: %s", candidate, exc)
        return []


def _extract_roles(request: Request) -> Iterable[str]:
    """
    Best-effort role extraction. Tries common locations used by apps:
    - request.state.user.roles
    - request.state.roles
    - request.scope["user"].roles (set by AuthenticationMiddleware)
    - request.headers["X-Roles"] as comma-separated fallback
    Adjust this function to your actual auth pipeline.
    """

    roles: list[str] = []
    state = getattr(request, "state", None)
    if state is not None:
        user = getattr(state, "user", None)
        roles = _normalize_roles(getattr(user, "roles", None))
        if not roles:
            roles = _normalize_roles(getattr(state, "roles", None))

    if not roles:
        scope = request.scope if isinstance(request.scope, dict) else {}
        scope_user = scope.get("user") if isinstance(scope, dict) else None
        if scope_user is not None:
            roles = _normalize_roles(getattr(scope_user, "roles", None))

    if not roles:
        header = request.headers.get("X-Roles")
        if header:
            roles = [r.strip() for r in header.split(",") if r.strip()]

    admin_key = request.headers.get("X-Admin-Key") or request.headers.get("x-admin-key")
    if admin_key:
        settings = _load_settings_safe()
        configured = getattr(settings, "admin_api_key", None) if settings else None
        if configured and str(admin_key) == str(configured) and ROLE_ADMIN not in roles:
            roles = [*roles, ROLE_ADMIN]
        elif admin_key and not configured:
            logger.debug("Admin key provided but no configured admin_api_key found")

    if not roles:
        settings = _load_settings_safe()
        if settings:
            env = str(getattr(settings, "env", "dev")).lower()
            if env != "prod":
                roles = [ROLE_ADMIN]
        else:
            logger.debug("Settings unavailable; moderation dev fallback skipped")
    return roles


def _roles_to_scopes(roles: Iterable[str]) -> set[str]:
    scopes: set[str] = set()
    for r in roles:
        scopes |= ROLE_TO_SCOPES.get(r, set())
    return scopes


def require_scopes(*needed_scopes: str) -> Callable:
    """FastAPI dependency to enforce required scopes.

    Example:
        @router.get("/items", dependencies=[Depends(require_scopes("moderation:content:read"))])
    """

    async def _dep(
        request: Request, _cred: HTTPAuthorizationCredentials | None = Depends(security)
    ):
        roles = _extract_roles(request)
        user_scopes = _roles_to_scopes(roles)
        missing = [s for s in needed_scopes if s not in user_scopes]
        if missing:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "missing_scopes": missing,
                    "roles": roles,
                },
            )

    return _dep


__all__ = [
    "ROLE_ADMIN",
    "ROLE_MODERATOR",
    "ROLE_EDITOR",
    "ROLE_USER",
    "require_scopes",
    "ROLE_TO_SCOPES",
]
