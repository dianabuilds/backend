import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.log_filters import request_id_var, user_id_var


logger = logging.getLogger("app.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        req_id = str(uuid.uuid4())
        token_req = request_id_var.set(req_id)
        token_user = user_id_var.set("-")

        start = time.perf_counter()
        path = request.url.path
        method = request.method

        try:
            uid = getattr(request.state, "user_id", None)
            if uid:
                user_id_var.set(str(uid))
        except Exception:  # pragma: no cover - safety
            pass

        if settings.logging.requests:
            logger.info(f"REQUEST {method} {path}")

        try:
            response: Response = await call_next(request)
        except Exception:
            if settings.logging.include_traceback:
                logger.exception("UNHANDLED_EXCEPTION")
            else:  # pragma: no cover - rarely configured
                logger.error("UNHANDLED_EXCEPTION")
            raise
        finally:
            dur_ms = int((time.perf_counter() - start) * 1000)
            level = (
                logging.WARNING
                if dur_ms >= settings.logging.slow_request_ms
                else logging.INFO
            )
            logger.log(level, f"RESPONSE {method} {path} {dur_ms}ms")
            request_id_var.reset(token_req)
            user_id_var.reset(token_user)

        response.headers["X-Request-Id"] = req_id
        return response

