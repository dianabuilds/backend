from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Добавляет браузерные заголовки безопасности и CSP.
    В продакшне включает HSTS при HTTPS.
    Для Swagger/Redoc ослабляем политику и разрешаем загрузку ресурсов с https: CDN.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Базовые secure-заголовки
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        # Выбираем CSP в зависимости от пути
        path = request.url.path or ""
        is_docs = path.startswith("/docs") or path.startswith("/redoc")

        if not headers.get("Content-Security-Policy"):
            if is_docs:
                # Swagger/Redoc используют inline bootstrap и, по умолчанию, CDN (https:)
                csp = (
                    "default-src 'self'; "
                    "base-uri 'self'; "
                    "frame-ancestors 'none'; "
                    "img-src 'self' data: blob: https:; "
                    "font-src 'self' data: https:; "
                    "script-src 'self' 'unsafe-inline' https:; "
                    "style-src 'self' 'unsafe-inline' https:; "
                    "connect-src 'self' https: ws: wss:; "
                    "worker-src 'self' blob:; "
                    "form-action 'self'"
                )
            else:
                csp = (
                    "default-src 'self'; "
                    "base-uri 'self'; "
                    "frame-ancestors 'none'; "
                    "img-src 'self' data: blob:; "
                    "font-src 'self' data:; "
                    "script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "connect-src 'self' https: ws: wss:; "
                    "form-action 'self'"
                )
            headers["Content-Security-Policy"] = csp

        # HSTS только в продакшне и только при https
        try:
            is_https = request.url.scheme == "https"
        except Exception:
            is_https = False
        if settings.is_production and is_https:
            headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )

        return response
