from __future__ import annotations

from secrets import token_urlsafe
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel.config import settings
from app.kernel.errors import http_error
from app.domains.auth.application.auth_service import AuthService
from app.domains.auth.application.ports.mail_port import IMailer
from app.domains.auth.application.ports.ratelimit_port import IRateLimiter
from app.domains.auth.application.ports.hasher import IPasswordHasher
from app.domains.auth.application.ports.tokens import ITokenService as ITokensPort
from app.domains.auth.application.ports.user_repo import IUserRepository
from app.domains.auth.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.domains.auth.infrastructure.nonce_store import NonceStore
from app.domains.auth.infrastructure.verification_token_store import (
    VerificationTokenStore,
)
from app.domains.auth.infrastructure.password_reset_store import PasswordResetStore
from app.kernel.db import get_db
from app.schemas.auth import (
    EVMVerify,
    LoginResponse,
    LoginSchema,
    SignupSchema,
    Token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_container(request: Request):
    return request.app.state.container


def _get_tokens(container=Depends(_get_container)) -> ITokensPort:
    return container.resolve(ITokensPort)


def _get_rate(container=Depends(_get_container)) -> IRateLimiter:
    return container.resolve(IRateLimiter)


def _get_mailer(container=Depends(_get_container)) -> IMailer:
    return container.resolve(IMailer)


def _get_hasher(container=Depends(_get_container)) -> IPasswordHasher:
    return container.resolve(IPasswordHasher)

def _get_nonce_store(container=Depends(_get_container)) -> NonceStore:
    return container.resolve(NonceStore)


def _get_verification_store(container=Depends(_get_container)) -> VerificationTokenStore:
    return container.resolve(VerificationTokenStore)


def _get_auth_service(
    tokens: ITokensPort = Depends(_get_tokens),
    vstore: VerificationTokenStore = Depends(_get_verification_store),
    nstore: NonceStore = Depends(_get_nonce_store),
    rstore: PasswordResetStore = Depends(lambda container=Depends(_get_container): container.resolve(PasswordResetStore)),
    hasher: IPasswordHasher = Depends(_get_hasher),
) -> AuthService:
    return AuthService(tokens, vstore, nstore, rstore, hasher)


def _get_user_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> IUserRepository:
    return SqlAlchemyUserRepository(db)

# Reusable dependency for refresh token body parsing
_token_body = Body(default_factory=Token)
# Reusable dependency for Authorization header
_auth_header = Header()


async def _login_rate_limit(request: Request, response: Response, rate: IRateLimiter = Depends(_get_rate)):
    key = (
        "login_json"
        if request.headers.get("content-type", "").startswith("application/json")
        else "login"
    )
    dep = rate.dependency(key)
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
                "application/x-www-form-urlencoded": {"schema": LoginSchema.model_json_schema()},
            },
        }
    },
)
async def login(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    svc: AuthService = Depends(_get_auth_service),
    repo: IUserRepository = Depends(_get_user_repo),
) -> LoginResponse:
    payload = await LoginSchema.from_request(request)
    tokens = await svc.login(db, payload, repo)
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


router.add_api_route(
    "/signin",
    login,
    methods=["POST"],
    response_model=LoginResponse,
    dependencies=[Depends(_login_rate_limit)],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": LoginSchema.model_json_schema()},
                "application/x-www-form-urlencoded": {"schema": LoginSchema.model_json_schema()},
            },
        }
    },
)


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    request: Request,
    response: Response,
    payload: Token = _token_body,
    svc: AuthService = Depends(_get_auth_service),
) -> LoginResponse:
    token = payload.token or request.cookies.get("refresh_token")
    if not token:
        raise http_error(401, "Invalid refresh token")
    result = await svc.refresh(Token(token=token))
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


async def _signup_rate_limit(request: Request, response: Response, rate: IRateLimiter = Depends(_get_rate)):
    dep = rate.dependency("signup")
    return await dep(request, response)


@router.post("/signup", dependencies=[Depends(_signup_rate_limit)])
async def signup(
    payload: SignupSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    svc: AuthService = Depends(_get_auth_service),
    mailer: IMailer = Depends(_get_mailer),
    repo: IUserRepository = Depends(_get_user_repo),
) -> dict[str, Any]:
    return await svc.signup(db, payload, mailer, repo)


@router.get("/verify")
async def verify_email(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Query(...)],
    rate: IRateLimiter = Depends(_get_rate),
    svc: AuthService = Depends(_get_auth_service),
    repo: IUserRepository = Depends(_get_user_repo),
) -> dict[str, Any]:
    if not token:
        raise http_error(400, "Token required")
    return await svc.verify_email(db, token, repo)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str, _auth_header] = "",
    rate: IRateLimiter = Depends(_get_rate),
    svc: AuthService = Depends(_get_auth_service),
    repo: IUserRepository = Depends(_get_user_repo),
) -> dict[str, Any]:
    token = authorization.replace("Bearer ", "")
    return await svc.change_password(db, token, payload.old_password, payload.new_password, repo)


@router.post("/logout")
async def logout(svc: AuthService = Depends(_get_auth_service)) -> dict[str, Any]:
    return await svc.logout()


class ResetRequestIn(BaseModel):
    email: str


async def _reset_request_rate_limit(request: Request, response: Response, rate: IRateLimiter = Depends(_get_rate)):
    dep = rate.dependency("reset_request")
    return await dep(request, response)


@router.post("/reset/request", dependencies=[Depends(_reset_request_rate_limit)])
async def reset_request(
    payload: ResetRequestIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    svc: AuthService = Depends(_get_auth_service),
    mailer: IMailer = Depends(_get_mailer),
    repo: IUserRepository = Depends(_get_user_repo),
) -> dict[str, Any]:
    return await svc.request_password_reset(db, payload.email, mailer, repo)


class ResetConfirmIn(BaseModel):
    token: str
    new_password: str


async def _reset_confirm_rate_limit(request: Request, response: Response, rate: IRateLimiter = Depends(_get_rate)):
    dep = rate.dependency("reset_confirm")
    return await dep(request, response)


@router.post("/reset/confirm", dependencies=[Depends(_reset_confirm_rate_limit)])
async def reset_confirm(
    payload: ResetConfirmIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    svc: AuthService = Depends(_get_auth_service),
    repo: IUserRepository = Depends(_get_user_repo),
) -> dict[str, Any]:
    return await svc.confirm_password_reset(db, payload.token, payload.new_password, repo)


@router.get("/evm/nonce")
async def evm_nonce(
    user_id: Annotated[str, Query(..., description="User ID")],
    rate: IRateLimiter = Depends(_get_rate),
    svc: AuthService = Depends(_get_auth_service),
) -> dict[str, Any]:
    return await svc.evm_nonce(user_id)


@router.post("/evm/verify")
async def evm_verify(
    payload: EVMVerify,
    rate: IRateLimiter = Depends(_get_rate),
    svc: AuthService = Depends(_get_auth_service),
) -> dict[str, Any]:
    return await svc.evm_verify(payload)


__all__ = ["router"]

