from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF: применяем только к cookie-сессиям (без Bearer).

    Дополнительно: если запрос пришёл с того же источника (Origin/Referer совпадает
    с базовым URL приложения), то CSRF‑заголовок не требуем. Это позволяет работать
    со Swagger UI и другими same-origin клиентами без дополнительной настройки,
    сохраняя защиту от межсайтовых запросов (CSRF).
    """

    @staticmethod
    def _is_same_origin(request: Request) -> bool:
        base = urlparse(str(request.base_url))
        origin = request.headers.get("Origin")
        if origin:
            o = urlparse(origin)
            return (o.scheme, o.hostname, o.port or (443 if o.scheme == "https" else 80)) == (
                base.scheme,
                base.hostname,
                base.port or (443 if base.scheme == "https" else 80),
            )
        # В большинстве браузеров для same-origin POST Referer указывает полный URL
        referer = request.headers.get("Referer") or request.headers.get("Referrer")
        if referer:
            r = urlparse(referer)
            return (r.scheme, r.hostname, r.port or (443 if r.scheme == "https" else 80)) == (
                base.scheme,
                base.hostname,
                base.port or (443 if base.scheme == "https" else 80),
            )
        # Нет Origin/Referer — консервативно требуем CSRF (считаем не same-origin)
        return False

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            path = request.url.path or ""
            # Исключаем auth-роуты (кроме logout)
            if not path.startswith("/auth") or path == "/auth/logout":
                # Если используется Bearer Authorization — CSRF не требуем
                auth = request.headers.get("Authorization")
                has_bearer = bool(auth and auth.lower().startswith("bearer "))

                # Требуем CSRF только если есть cookie-сессия (access_token) и нет Bearer
                has_session_cookie = bool(request.cookies.get("access_token"))

                if has_session_cookie and not has_bearer:
                    # Для same-origin запросов токен не обязателен
                    if not self._is_same_origin(request):
                        csrf_cookie = request.cookies.get("XSRF-TOKEN")
                        header = request.headers.get("X-CSRF-Token") or request.headers.get("X-XSRF-TOKEN")
                        if not csrf_cookie or not header or csrf_cookie != header:
                            return JSONResponse(
                                {"detail": "CSRF token missing or invalid"}, status_code=403
                            )
        return await call_next(request)

