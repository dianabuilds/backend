from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
import sentry_sdk

from app.core.errors import DomainError
from app.core.log_filters import request_id_var
from app.security.exceptions import AuthError

logger = logging.getLogger("app.errors")


# Map HTTP status codes to our unified error codes.
# Codes are intentionally whitelisted to keep the surface small and predictable.
ERROR_CODE_MAP = {
    400: "BAD_REQUEST",
    401: "AUTH_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


def _build_body(
    code: str,
    message: str,
    details: Any = None,
    field_errors: Any = None,
) -> dict:
    """Construct the error response body in a unified format."""

    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "field_errors": field_errors,
        },
        "request_id": request_id_var.get(),
    }


def _json_response(status_code: int, body: dict) -> JSONResponse:
    response = JSONResponse(status_code=status_code, content=jsonable_encoder(body))
    req_id = request_id_var.get()
    if req_id:
        response.headers["X-Request-Id"] = req_id
    return response


async def auth_exception_handler(request: Request, exc: AuthError) -> JSONResponse:
    body = _build_body(exc.code, exc.message)
    logger.warning(
        "access_denied path=%s method=%s reason_code=%s user_id=%s role=%s request_id=%s",
        request.url.path,
        request.method,
        exc.code,
        exc.user_id,
        exc.role,
        request_id_var.get(),
    )
    response = _json_response(exc.status_code, body)
    if exc.status_code == 401:
        response.headers["WWW-Authenticate"] = "Bearer"
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = ERROR_CODE_MAP.get(exc.status_code, "HTTP_ERROR")
    body = _build_body(code, str(exc.detail))
    if exc.status_code >= 500:
        sentry_sdk.capture_exception(exc)
        logger.error("HTTPException %s", exc)
    response = _json_response(exc.status_code, body)
    if exc.status_code == 401:
        response.headers["WWW-Authenticate"] = "Bearer"
    return response


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    body = _build_body(
        "VALIDATION_ERROR",
        "Validation error",
        details=None,
        field_errors=exc.errors(),
    )
    return _json_response(422, body)


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    body = _build_body(exc.code, exc.message, exc.details)
    return _json_response(exc.status_code, body)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    sentry_sdk.capture_exception(exc)
    message = str(exc) or "Internal server error"
    body = _build_body("INTERNAL_ERROR", message)
    return _json_response(500, body)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AuthError, auth_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
