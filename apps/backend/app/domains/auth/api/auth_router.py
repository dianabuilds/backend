from __future__ import annotations

from secrets import token_urlsafe
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db.session import get_db
from app.core.errors import http_error
from app.domains.auth.application.auth_service import AuthService
from app.domains.auth.infrastructure.mail_adapter import LegacyMailAdapter
from app.domains.auth.infrastructure.nonce_store import NonceStore
from app.domains.auth.infrastructure.ratelimit_adapter import CoreRateLimiter
from app.domains.auth.infrastructure.token_adapter import CoreTokenAdapter
from app.domains.auth.infrastructure.verification_token_store import (
    VerificationTokenStore,
)
from app.schemas.auth import (
    EVMVerify,
    LoginResponse,
    LoginSchema,
    SignupSchema,
    Token,
)

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore

router = APIRouter(prefix="/auth", tags=["auth"])

_tokens = CoreTokenAdapter()
_rate = CoreRateLimiter()
_mailer = LegacyMailAdapter()

# Redis backend for nonces and verification tokens. In development and tests
# we want the router to load even if Redis is not available, so fall back to
# ``fakeredis`` when configuration or the real library is missing.
try:  # pragma: no cover - optional dependency
    import fakeredis.aioredis as fakeredis  # type: ignore
except Exception:  # pragma: no cover
    fakeredis = None  # type: ignore

if settings.redis_url and not settings.redis_url.startswith("fakeredis://"):
    if redis is not None:
        try:
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:  # pragma: no cover - connection issues
            if fakeredis is None:
                raise
            _redis = fakeredis.FakeRedis(decode_responses=True)
    else:  # redis library not installed
        if fakeredis is None:
            raise RuntimeError("redis library is not installed")
        _redis = fakeredis.FakeRedis(decode_responses=True)
else:  # No URL provided or explicit fakeredis://
    if fakeredis is None:
        raise RuntimeError("Redis URL is not configured")
    _redis = fakeredis.FakeRedis(decode_responses=True)

_nonce_store = NonceStore(_redis, settings.auth.nonce_ttl)
_verification_store = VerificationTokenStore(
    _redis, settings.auth.verification_token_ttl
)
_svc = AuthService(_tokens, _verification_store, _nonce_store)


async def _login_rate_limit(request: Request, response: Response):
    key = (
        "login_json"
        if request.headers.get("content-type", "").startswith("application/json")
        else "login"
    )
    dep = _rate.dependency(key)
    return await dep(request, response)


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(_login_rate_limit)],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": LoginSchema.model_json_schema()},
                "application/x-www-form-urlencoded": {
                    "schema": LoginSchema.model_json_schema()
                },
            },
        }
    },
)
async def login(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
) -> LoginResponse:
    payload = await LoginSchema.from_request(request)
    tokens = await _svc.login(db, payload)
    # Issue authentication cookies for browser flows
    response.set_cookie(
        "access_token",
        tokens.access_token,
        max_age=settings.jwt.expiration,
        path="/",
    )
    if tokens.refresh_token:
        response.set_cookie(
            "refresh_token",
            tokens.refresh_token,
            max_age=settings.jwt.refresh_expiration,
            path="/",
        )
    # Also issue a non-HttpOnly CSRF cookie so SPA can read it and send header
    # Double-submit cookie name/header are configurable in settings.csrf
    try:
        csrf_value = token_urlsafe(32)
        response.set_cookie(
            settings.csrf.cookie_name,
            csrf_value,
            max_age=settings.jwt.expiration,
            path="/",
            httponly=False,
            samesite="Lax",
            secure=settings.is_production,
        )
        # Include token in JSON for clients that sync it from response body
        tokens.csrf_token = csrf_value
    except Exception:
        # If something goes wrong, do not break login flow
        pass
    return tokens


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    request: Request,
    response: Response,
    payload: Annotated[Token, Body(default=Token())] = ...,
) -> LoginResponse:
    token = payload.token or request.cookies.get("refresh_token")
    if not token:
        raise http_error(401, "Invalid refresh token")
    result = await _svc.refresh(Token(token=token))
    response.set_cookie(
        "access_token",
        result.access_token,
        max_age=settings.jwt.expiration,
        path="/",
    )
    if result.refresh_token:
        response.set_cookie(
            "refresh_token",
            result.refresh_token,
            max_age=settings.jwt.refresh_expiration,
            path="/",
        )
    # Rotate CSRF token alongside access refresh to keep things in sync
    try:
        csrf_value = token_urlsafe(32)
        response.set_cookie(
            settings.csrf.cookie_name,
            csrf_value,
            max_age=settings.jwt.expiration,
            path="/",
            httponly=False,
            samesite="Lax",
            secure=settings.is_production,
        )
        result.csrf_token = csrf_value
    except Exception:
        pass
    return result


@router.post("/signup", dependencies=[Depends(_rate.dependency("signup"))])
async def signup(
    payload: SignupSchema, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    return await _svc.signup(db, payload, _mailer)


@router.get("/verify", dependencies=[Depends(_rate.dependency("verify"))])
async def verify_email(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Query(...)] = ...,
) -> dict[str, Any]:
    if not token:
        raise http_error(400, "Token required")
    return await _svc.verify_email(db, token)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


@router.post(
    "/change-password", dependencies=[Depends(_rate.dependency("change_password"))]
)
async def change_password(
    payload: ChangePasswordIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, Header(default="")] = ...,
) -> dict[str, Any]:
    token = authorization.replace("Bearer ", "")
    return await _svc.change_password(
        db, token, payload.old_password, payload.new_password
    )


@router.post("/logout")
async def logout() -> dict[str, Any]:
    return await _svc.logout()


@router.get("/evm/nonce", dependencies=[Depends(_rate.dependency("evm_nonce"))])
async def evm_nonce(
    user_id: Annotated[str, Query(..., description="User ID")] = ...,
) -> dict[str, Any]:
    return await _svc.evm_nonce(user_id)


@router.post("/evm/verify", dependencies=[Depends(_rate.dependency("evm_verify"))])
async def evm_verify(payload: EVMVerify) -> dict[str, Any]:
    return await _svc.evm_verify(payload)


__all__ = ["router"]
