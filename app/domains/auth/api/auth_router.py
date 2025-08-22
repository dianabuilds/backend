from __future__ import annotations

import hashlib
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.auth.application.auth_service import AuthService
from app.domains.auth.infrastructure.token_adapter import CoreTokenAdapter
from app.domains.auth.infrastructure.ratelimit_adapter import CoreRateLimiter
from app.domains.auth.infrastructure.mail_adapter import LegacyMailAdapter
from app.domains.users.schemas.auth import LoginSchema, LoginResponse, Token, SignupSchema, EVMVerify

router = APIRouter(prefix="/auth", tags=["auth"])

_tokens = CoreTokenAdapter()
_rate = CoreRateLimiter()
_mailer = LegacyMailAdapter()
_svc = AuthService(_tokens)

# In-memory store для EVM nonce (одноразовые)
_nonce_store: dict[str, str] = {}


@router.post("/login", response_model=LoginResponse, dependencies=[Depends(_rate.dependency("login"))])
async def login(payload: LoginSchema, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    return await _svc.login(db, payload)


@router.post("/refresh", response_model=LoginResponse)
async def refresh(payload: Token) -> LoginResponse:
    return await _svc.refresh(payload)


@router.post("/signup", dependencies=[Depends(_rate.dependency("signup"))])
async def signup(payload: SignupSchema, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    return await _svc.signup(db, payload, _mailer)


class VerifyIn(BaseModel):
    token: str


@router.post("/verify", dependencies=[Depends(_rate.dependency("verify"))])
async def verify_email(payload: VerifyIn, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    if not payload.token:
        raise HTTPException(status_code=400, detail="Token required")
    return await _svc.verify_email(db, payload.token)


class ChangePasswordIn(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str


@router.post("/change_password", dependencies=[Depends(_rate.dependency("change_password"))])
async def change_password(payload: ChangePasswordIn, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    return await _svc.change_password(db, payload.email, payload.old_password, payload.new_password)


@router.post("/logout")
async def logout() -> Dict[str, Any]:
    return await _svc.logout()


@router.get("/evm/nonce", dependencies=[Depends(_rate.dependency("evm_nonce"))])
async def evm_nonce(user_id: str = Query(..., description="User ID")) -> Dict[str, Any]:
    return await _svc.evm_nonce(_nonce_store, user_id)


@router.post("/evm/verify", dependencies=[Depends(_rate.dependency("evm_verify"))])
async def evm_verify(payload: EVMVerify) -> Dict[str, Any]:
    return await _svc.evm_verify(_nonce_store, payload)


__all__ = ["router"]
