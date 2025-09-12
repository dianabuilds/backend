from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.kernel.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        path = request.url.path or ""
        is_docs = path.startswith("/docs") or path.startswith("/redoc")

        if not headers.get("Content-Security-Policy"):
            if is_docs:
                csp = (
                    "default-src 'self'; "
                    "base-uri 'self'; "
                    "frame-ancestors 'none'; "
                    "img-src 'self' data: blob: https:; "
                    "font-src 'self' data: https:; "
                    "script-src 'self' https:; "
                    "style-src 'self' 'unsafe-inline' https:; "
                    "connect-src 'self' https: ws: wss:; "
                    "worker-src 'self' blob:; "
                    "form-action 'self'"
                )
            else:
                if settings.is_production:
                    img_src = "img-src 'self' data: blob:; "
                    connect_src = "connect-src 'self' https: ws: wss:; "
                else:
                    img_src = "img-src 'self' data: blob: http: https:; "
                    connect_src = "connect-src 'self' http: https: ws: wss:; "
                csp = (
                    "default-src 'self'; "
                    "base-uri 'self'; "
                    "frame-ancestors 'none'; "
                    f"{img_src}"
                    "font-src 'self' data:; "
                    "script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    f"{connect_src}"
                    "form-action 'self'"
                )
            headers["Content-Security-Policy"] = csp

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


__all__ = ["SecurityHeadersMiddleware"]
