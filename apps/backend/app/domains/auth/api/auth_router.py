from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request
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

if settings.auth.redis_url and settings.auth.redis_url.startswith("fakeredis://"):
    import fakeredis.aioredis as fakeredis  # type: ignore

    _redis = fakeredis.FakeRedis(decode_responses=True)
else:
    if redis is None:  # pragma: no cover - requires redis
        raise RuntimeError("redis library is not installed")
    if settings.auth.redis_url is None:
        raise RuntimeError("Redis URL is not configured")
    _redis = redis.from_url(settings.auth.redis_url, decode_responses=True)

_nonce_store = NonceStore(_redis, settings.auth.nonce_ttl)
_verification_store = VerificationTokenStore(
    _redis, settings.auth.verification_token_ttl
)
_svc = AuthService(_tokens, _verification_store, _nonce_store)


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(_rate.dependency("login"))],
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
) -> LoginResponse:
    payload = await LoginSchema.from_request(request)
    return await _svc.login(db, payload)


@router.post("/refresh", response_model=LoginResponse)
async def refresh(payload: Token) -> LoginResponse:
    return await _svc.refresh(payload)


@router.post("/signup", dependencies=[Depends(_rate.dependency("signup"))])
async def signup(
    payload: SignupSchema, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    return await _svc.signup(db, payload, _mailer)


@router.get("/verify", dependencies=[Depends(_rate.dependency("verify"))])
async def verify_email(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: str = Query(...),
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
    authorization: str = Header(default=""),
) -> dict[str, Any]:
    token = authorization.replace("Bearer ", "")
    return await _svc.change_password(
        db, token, payload.old_password, payload.new_password
    )


@router.post("/logout")
async def logout() -> dict[str, Any]:
    return await _svc.logout()


@router.get("/evm/nonce", dependencies=[Depends(_rate.dependency("evm_nonce"))])
async def evm_nonce(user_id: str = Query(..., description="User ID")) -> dict[str, Any]:
    return await _svc.evm_nonce(user_id)


@router.post("/evm/verify", dependencies=[Depends(_rate.dependency("evm_verify"))])
async def evm_verify(payload: EVMVerify) -> dict[str, Any]:
    return await _svc.evm_verify(payload)


__all__ = ["router"]
