from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Простой лимит по размеру тела запроса на основе заголовка Content-Length.
    Если заголовок отсутствует (chunked), лимит не применяется (можно развить при необходимости).
    """

    def __init__(self, app, max_bytes: int | None = None):
        super().__init__(app)
        # По умолчанию 2 МБ, либо берём из настроек при наличии
        default_limit = 2 * 1024 * 1024
        security = getattr(settings, "security", None)
        configured = getattr(security, "max_request_body_bytes", None) if security else None
        self.max_bytes = int(max_bytes or configured or default_limit)

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            cl = request.headers.get("content-length")
            if cl:
                try:
                    length = int(cl)
                except ValueError:
                    length = None
                if length is not None and length > self.max_bytes:
                    return JSONResponse(
                        {"detail": "Request body too large"},
                        status_code=413,
                    )
        return await call_next(request)
