from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, Response

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore
from secrets import token_urlsafe

from pydantic import BaseModel, Field, model_validator

from apps.backend import get_container
from domains.platform.iam.application.auth_service import AuthError, LoginIn


class LoginSchema(BaseModel):
    """Accept either `login` or legacy `email` field for username/email auth."""

    login: str | None = Field(default=None, description="Username or email")
    email: str | None = Field(default=None, description="Deprecated alias for login")
    password: str = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_login(self) -> LoginSchema:
        identifier = (self.login or self.email or "").strip()
        if not identifier:
            raise ValueError("login_required")
        self.login = identifier
        return self


class SignupSchema(BaseModel):
    email: str
    password: str | None = None


class Token(BaseModel):
    token: str


class EVMVerify(BaseModel):
    message: str
    signature: str
    wallet_address: str


DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/auth", tags=["auth"])

    token_body = Body(default_factory=Token)
    # auth header placeholder removed; not used

    @router.post(
        "/login",
        dependencies=([Depends(RateLimiter(times=5, seconds=60))] if RateLimiter else []),
    )
    async def login(req: Request, payload: LoginSchema, response: Response) -> dict[str, Any]:
        c = get_container(req)
        try:
            result = await c.iam.service.login(
                LoginIn(login=payload.login, password=payload.password)
            )
        except AuthError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e
        pair = result.tokens
        identity = result.user
        auth_source = result.source
        s = c.settings
        # Cookies: access + refresh (HttpOnly)
        # Derive host for cookie scoping (host-only cookies by default).
        # Explicit Domain is omitted to keep cookies host-only and avoid 127.0.0.1/localhost mismatch.
        response.set_cookie(
            "access_token",
            pair.access_token,
            max_age=int(s.auth_jwt_expires_min) * 60,
            path="/",
            httponly=True,
            samesite="lax",
            secure=(s.env == "prod"),
        )
        if pair.refresh_token:
            response.set_cookie(
                "refresh_token",
                pair.refresh_token,
                max_age=int(s.auth_jwt_refresh_expires_days) * 86400,
                path="/",
                httponly=True,
                samesite="lax",
                secure=(s.env == "prod"),
            )
        # CSRF cookie (non-HttpOnly)
        csrf_value = token_urlsafe(32)
        response.set_cookie(
            s.auth_csrf_cookie_name,
            csrf_value,
            max_age=int(s.auth_jwt_expires_min) * 60,
            path="/",
            httponly=False,
            samesite="lax",
            secure=(s.env == "prod"),
        )
        # Audit login
        try:
            await c.audit.service.log(
                actor_id=str(identity.id),
                action="auth.login",
                resource_type="user",
                resource_id=str(identity.id),
                ip=req.client.host if req and req.client else None,
                user_agent=req.headers.get("user-agent"),
            )
        except Exception:
            pass
        return {
            "access_token": pair.access_token,
            "refresh_token": pair.refresh_token,
            "csrf_token": csrf_value,
            "auth": {"source": auth_source},
            "user": {
                "id": identity.id,
                "email": identity.email,
                "username": identity.username,
                "role": identity.role,
                "roles": ([identity.role] if identity.role else []),
                "is_active": identity.is_active,
            },
        }

    @router.post(
        "/refresh",
        dependencies=([Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []),
    )
    async def refresh(
        req: Request, payload: Token = token_body, response: Response = None
    ) -> dict[str, Any]:
        c = get_container(req)
        pair = await c.iam.service.refresh(payload.token)
        s = c.settings
        if response is not None:
            response.set_cookie(
                "access_token",
                pair.access_token,
                max_age=int(s.auth_jwt_expires_min) * 60,
                path="/",
                httponly=True,
                samesite="lax",
                secure=(s.env == "prod"),
            )
            if pair.refresh_token:
                response.set_cookie(
                    "refresh_token",
                    pair.refresh_token,
                    max_age=int(s.auth_jwt_refresh_expires_days) * 86400,
                    path="/",
                    httponly=True,
                    samesite="Lax",
                    secure=(s.env == "prod"),
                )
            # Rotate CSRF
            csrf_value = token_urlsafe(32)
            response.set_cookie(
                s.auth_csrf_cookie_name,
                csrf_value,
                max_age=int(s.auth_jwt_expires_min) * 60,
                path="/",
                httponly=False,
                samesite="Lax",
                secure=(s.env == "prod"),
            )
        return {"access_token": pair.access_token, "refresh_token": pair.refresh_token}

    @router.post(
        "/signup",
        dependencies=([Depends(RateLimiter(times=3, seconds=3600))] if RateLimiter else []),
    )
    async def signup(req: Request, payload: SignupSchema) -> dict[str, Any]:
        c = get_container(req)
        return await c.iam.service.signup(payload)  # type: ignore[arg-type]

    @router.post("/logout")
    async def logout(req: Request, response: Response) -> dict[str, Any]:
        c = get_container(req)
        s = c.settings
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        response.delete_cookie(s.auth_csrf_cookie_name, path="/")
        return {"ok": True}

    @router.get("/verify")
    async def verify_email(req: Request, token: str = Query(...)) -> dict[str, Any]:
        c = get_container(req)
        return await c.iam.service.verify_email(token)

    @router.get(
        "/evm/nonce",
        dependencies=([Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []),
    )
    async def evm_nonce(req: Request, user_id: str = Query(...)) -> dict[str, Any]:
        c = get_container(req)
        return await c.iam.service.evm_nonce(user_id)

    @router.post(
        "/evm/verify",
        dependencies=([Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []),
    )
    async def evm_verify(req: Request, payload: EVMVerify, response: Response) -> dict[str, Any]:
        c = get_container(req)
        try:
            pair = await c.iam.service.evm_verify(payload)  # type: ignore[arg-type]
        except Exception as e:
            return {"ok": False, "error": str(e)}
        s = c.settings
        response.set_cookie(
            "access_token",
            pair.access_token,
            max_age=int(s.auth_jwt_expires_min) * 60,
            path="/",
            httponly=True,
            samesite="lax",
            secure=(s.env == "prod"),
        )
        if pair.refresh_token:
            response.set_cookie(
                "refresh_token",
                pair.refresh_token,
                max_age=int(s.auth_jwt_refresh_expires_days) * 86400,
                path="/",
                httponly=True,
                samesite="Lax",
                secure=(s.env == "prod"),
            )
        csrf_value = token_urlsafe(32)
        response.set_cookie(
            s.auth_csrf_cookie_name,
            csrf_value,
            max_age=int(s.auth_jwt_expires_min) * 60,
            path="/",
            httponly=False,
            samesite="Lax",
            secure=(s.env == "prod"),
        )
        return {
            "ok": True,
            "access_token": pair.access_token,
            "refresh_token": pair.refresh_token,
            "csrf_token": csrf_value,
        }

    return router
