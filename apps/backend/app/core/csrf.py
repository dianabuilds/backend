import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse

from app.core.config import settings


logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF middleware.

    Проверка активируется только для мутирующих методов и когда запрос
    использует cookie-сессию. Bearer‑токены игнорируются, если не включено
    обязательное требование CSRF для Bearer.

    Если запрос пришёл с того же источника (Origin/Referer совпадает с базовым
    URL приложения), CSRF‑заголовок не требуется.
    """

    @staticmethod
    def _is_same_origin(request: Request) -> bool:
        base = urlparse(str(request.base_url))
        origin = request.headers.get("Origin")
        if origin:
            o = urlparse(origin)
            return (
                o.scheme,
                o.hostname,
                o.port or (443 if o.scheme == "https" else 80),
            ) == (
                base.scheme,
                base.hostname,
                base.port or (443 if base.scheme == "https" else 80),
            )
        # В большинстве браузеров для same-origin POST Referer указывает полный URL
        referer = request.headers.get("Referer") or request.headers.get("Referrer")
        if referer:
            r = urlparse(referer)
            return (
                r.scheme,
                r.hostname,
                r.port or (443 if r.scheme == "https" else 80),
            ) == (
                base.scheme,
                base.hostname,
                base.port or (443 if base.scheme == "https" else 80),
            )
        # Нет Origin/Referer — консервативно требуем CSRF (считаем не same-origin)
        return False

    async def dispatch(self, request: Request, call_next):
        if not settings.csrf.enabled:
            return await call_next(request)

        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            path = request.url.path or ""
            normalized_path = path.removeprefix("/api")
            if (
                normalized_path.startswith("/auth")
                and normalized_path != "/auth/logout"
            ) or any(
                normalized_path.startswith(p) or path.startswith(p)
                for p in settings.csrf.exempt_paths
            ):
                return await call_next(request)

            auth = request.headers.get("Authorization") or ""
            has_bearer = auth.lower().startswith("bearer ")
            session_cookies = {"access_token", "session"}
            has_session_cookie = any(
                name in request.cookies for name in session_cookies
            )

            if not has_session_cookie and not (
                has_bearer and settings.csrf.require_for_bearer
            ):
                return await call_next(request)

            if not self._is_same_origin(request):
                csrf_cookie = request.cookies.get(settings.csrf.cookie_name)
                header = request.headers.get(settings.csrf.header_name)
                if not csrf_cookie:
                    logger.info(
                        "CSRF reject: missing cookie %s", settings.csrf.cookie_name
                    )
                    return JSONResponse(
                        {"detail": "CSRF token missing or invalid"}, status_code=403
                    )
                if not header:
                    logger.info(
                        "CSRF reject: missing header %s", settings.csrf.header_name
                    )
                    return JSONResponse(
                        {"detail": "CSRF token missing or invalid"}, status_code=403
                    )
                if csrf_cookie != header:
                    logger.info("CSRF reject: token mismatch")
                    return JSONResponse(
                        {"detail": "CSRF token missing or invalid"}, status_code=403
                    )

        return await call_next(request)
