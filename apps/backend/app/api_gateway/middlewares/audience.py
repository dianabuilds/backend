from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, MutableMapping, Sequence

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from packages.core.config import Settings

try:  # pragma: no cover - import guard mirrors iam.security
    from jwt import PyJWTError  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from jwt import InvalidTokenError as PyJWTError  # type: ignore[attr-defined]


AudienceMatrix = Mapping[str, set[str]]
RoleMatrix = Mapping[str, set[str] | None]

DEFAULT_ALLOW_PREFIXES = (
    "/healthz",
    "/readyz",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
)
DEFAULT_ALLOW_PATHS = {"/", "/favicon.ico"}

AUDIENCE_ALLOW: AudienceMatrix = {
    "public": {"public", "shared", "admin", "ops"},
    "admin": {"admin", "shared"},
    "ops": {"ops", "shared"},
    "all": {"public", "admin", "ops", "shared"},
}

ROLE_ALLOW: RoleMatrix = {
    "public": None,
    "admin": {"editor", "moderator", "admin"},
    "ops": {"finance_ops", "admin"},
    "all": None,
}


class AudienceMiddleware(BaseHTTPMiddleware):
    """Guard requests so they match the configured contour/audience."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        contour: str,
        settings: Settings,
        allow_anonymous_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._logger = logging.getLogger(__name__)
        self._contour = contour.lower()
        self._settings = settings
        extra_paths = set(
            path.rstrip("/") or "/" for path in (allow_anonymous_paths or ())
        )
        self._allow_paths = DEFAULT_ALLOW_PATHS | extra_paths

    async def dispatch(self, request: Request, call_next):
        if self._contour == "all":
            return await call_next(request)
        if self._contour not in AUDIENCE_ALLOW:
            self._logger.debug(
                "Audience middleware disabled for contour=%s", self._contour
            )
            return await call_next(request)

        if self._is_exempt(request):
            return await call_next(request)

        if self._has_machine_key(request):
            role = "ops" if self._contour == "ops" else "admin"
            self._attach_context(request, source="api-key", role=role)
            return await call_next(request)

        token = self._extract_token(request)
        if token is None:
            if self._contour == "public":
                return await call_next(request)
            return JSONResponse(status_code=401, content={"detail": "missing_token"})

        claims = self._decode_claims(token)
        if claims is None:
            return JSONResponse(status_code=401, content={"detail": "invalid_token"})

        if not self._audience_allowed(claims):
            return JSONResponse(
                status_code=403, content={"detail": "audience_forbidden"}
            )

        if not self._role_allowed(claims):
            return JSONResponse(status_code=403, content={"detail": "role_forbidden"})

        self._attach_context(
            request,
            source="token",
            role=str(claims.get("role") or "").lower() or None,
            claims=claims,
        )
        return await call_next(request)

    def _normalize_path(self, request: Request) -> str:
        path = request.url.path or "/"
        return path if path == "/" else path.rstrip("/")

    def _is_exempt(self, request: Request) -> bool:
        path = self._normalize_path(request)
        if path in self._allow_paths:
            return True
        return any(path.startswith(prefix) for prefix in DEFAULT_ALLOW_PREFIXES)

    def _has_machine_key(self, request: Request) -> bool:
        if self._contour == "admin":
            secret = getattr(self._settings, "admin_api_key", None)
            header_name = "x-admin-key"
        elif self._contour == "ops":
            secret = getattr(self._settings, "ops_api_key", None)
            header_name = "x-ops-key"
        else:
            return False
        if not secret:
            return False
        header = request.headers.get(header_name) or request.headers.get(
            header_name.title()
        )
        return bool(header and header == secret.get_secret_value())

    def _extract_token(self, request: Request) -> str | None:
        token = request.cookies.get("access_token")
        if token:
            return token
        auth = request.headers.get("Authorization") or request.headers.get(
            "authorization"
        )
        if auth and auth.startswith("Bearer "):
            return auth[len("Bearer ") :].strip()
        return None

    def _decode_claims(self, token: str) -> MutableMapping[str, object] | None:
        try:
            decoded = jwt.decode(
                token,
                key=self._settings.auth_jwt_secret.get_secret_value(),
                algorithms=[self._settings.auth_jwt_algorithm],
                options={"require": ["exp", "sub"], "verify_aud": False},
            )
        except PyJWTError as exc:
            self._logger.debug("audience_middleware.decode_failed", exc_info=exc)
            return None
        return dict(decoded)

    def _audience_allowed(self, claims: Mapping[str, object]) -> bool:
        allowed = AUDIENCE_ALLOW[self._contour]
        raw = claims.get("audience") or claims.get("aud")
        if raw is None and self._contour == "public":
            return True
        values: set[str]
        if raw is None:
            values = set()
        elif isinstance(raw, str):
            values = {raw.lower()}
        elif isinstance(raw, Sequence):
            values = {str(item).lower() for item in raw}
        else:
            values = {str(raw).lower()}
        if not values and self._contour == "public":
            values = {"public"}
        return bool(values & allowed)

    def _role_allowed(self, claims: Mapping[str, object]) -> bool:
        allowed = ROLE_ALLOW[self._contour]
        if allowed is None:
            return True
        role = str(claims.get("role") or "").lower()
        return role in allowed

    def _attach_context(
        self,
        request: Request,
        *,
        source: str,
        role: str | None = None,
        claims: MutableMapping[str, object] | None = None,
    ) -> None:
        ctx: MutableMapping[str, object]
        try:
            ctx = getattr(request.state, "auth_context", {})  # type: ignore[attr-defined]
        except AttributeError:
            ctx = {}
        ctx = dict(ctx)
        ctx.setdefault("auth_via", source)
        if role:
            ctx["role"] = role
        ctx["audience"] = self._contour
        try:
            request.state.auth_context = ctx  # type: ignore[attr-defined]
            if claims is not None:
                request.state.auth_claims = claims  # type: ignore[attr-defined]
        except AttributeError:
            self._logger.debug(
                "Failed to persist auth context on request.state", exc_info=True
            )


__all__ = ["AudienceMiddleware"]
