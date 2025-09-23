from collections.abc import Callable, Iterable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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


# Simple role→scopes mapping. Adjust if your auth system differs.
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


security = HTTPBearer(auto_error=False)


def _extract_roles(request: Request) -> Iterable[str]:
    """
    Best-effort role extraction. Tries common locations used by apps:
    - request.state.user.roles
    - request.state.roles
    - request.user.roles
    - request.headers["X-Roles"] as comma-separated fallback
    Adjust this function to your actual auth pipeline.
    """
    roles = []
    state = getattr(request, "state", None)
    if state is not None:
        user = getattr(state, "user", None)
        if user is not None and hasattr(user, "roles"):
            roles = list(user.roles)
        elif hasattr(state, "roles"):
            roles = list(state.roles)
    # Avoid touching request.user property directly: it asserts when AuthenticationMiddleware is missing
    if not roles:
        try:
            scope_user = request.scope.get("user")  # set by AuthenticationMiddleware if present
        except Exception:
            scope_user = None
        if scope_user is not None and hasattr(scope_user, "roles"):
            try:
                roles = list(scope_user.roles)
            except Exception:
                roles = roles
    if not roles:
        header = request.headers.get("X-Roles")
        if header:
            roles = [r.strip() for r in header.split(",") if r.strip()]

    # Admin override via X-Admin-Key (dev/admin tooling): if header matches configured key, grant Admin role
    try:
        admin_key = request.headers.get("X-Admin-Key") or request.headers.get("x-admin-key")
        if admin_key:
            try:
                from packages.core.config import load_settings  # type: ignore

                settings = load_settings()
                configured = getattr(settings, "admin_api_key", None)
            except Exception:
                configured = None
            if configured and str(admin_key) == str(configured):
                if ROLE_ADMIN not in roles:
                    roles = list(roles) + [ROLE_ADMIN]
    except Exception:
        pass

    # Dev fallback: if environment is not 'prod' and roles still empty, grant Admin to ease local testing
    try:
        if not roles:
            from packages.core.config import load_settings  # type: ignore

            env = str(getattr(load_settings(), "env", "dev")).lower()
            if env != "prod":
                roles = [ROLE_ADMIN]
    except Exception:
        pass
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
