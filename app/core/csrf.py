from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFMiddleware(BaseHTTPMiddleware):
    """Simple double-submit cookie CSRF protection."""

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            path = request.url.path
            if not path.startswith("/auth") or path == "/auth/logout":
                csrf_cookie = request.cookies.get("XSRF-TOKEN")
                header = request.headers.get("X-CSRF-Token")
                if not csrf_cookie or not header or csrf_cookie != header:
                    return JSONResponse(
                        {"detail": "CSRF token missing or invalid"}, status_code=403
                    )
        return await call_next(request)

