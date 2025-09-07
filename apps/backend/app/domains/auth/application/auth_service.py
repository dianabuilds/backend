from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import http_error
from app.core.security import get_password_hash, verify_password
from app.domains.auth.application.ports.token_port import ITokenService
from app.domains.auth.infrastructure.nonce_store import NonceStore
from app.domains.auth.infrastructure.verification_token_store import (
    VerificationTokenStore,
)
from app.domains.users.infrastructure.models.user import User
from app.schemas.auth import (
    EVMVerify,
    LoginResponse,
    LoginSchema,
    SignupSchema,
    Token,
)


class AuthService:
    def __init__(
        self,
        tokens: ITokenService,
        verification_store: VerificationTokenStore,
        nonce_store: NonceStore,
    ) -> None:
        self._tokens = tokens
        self._verification_store = verification_store
        self._nonce_store = nonce_store

    async def login(self, db: AsyncSession, payload: LoginSchema) -> LoginResponse:
        q = await db.execute(
            select(User).where(or_(User.email == payload.login, User.username == payload.login))
        )
        user = q.scalars().first()
        if not user or not verify_password(payload.password, user.password_hash or ""):
            raise http_error(400, "Incorrect username or password")
        if not user.is_active:
            raise http_error(400, "Email not verified")
        user.last_login_at = datetime.utcnow()
        db.add(user)
        await db.commit()
        access = self._tokens.create_access_token(str(user.id))
        refresh = self._tokens.create_refresh_token(str(user.id))
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    async def refresh(self, payload: Token) -> LoginResponse:
        sub = self._tokens.verify_refresh_token(payload.token)
        if not sub:
            raise http_error(401, "Invalid refresh token")
        access = self._tokens.create_access_token(sub)
        refresh = self._tokens.create_refresh_token(sub)
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    async def signup(
        self, db: AsyncSession, payload: SignupSchema, mailer: object
    ) -> dict[str, Any]:
        q = await db.execute(select(User).where(User.username == payload.username))
        if q.scalars().first():
            raise http_error(400, "Username already taken")
        q = await db.execute(select(User).where(User.email == payload.email))
        if q.scalars().first():
            raise http_error(400, "Email already registered")
        user = User(
            email=payload.email,
            username=payload.username,
            password_hash=get_password_hash(payload.password),
            is_active=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        # Handle referral code (best-effort)
        try:
            if payload.referral_code:
                from app.domains.referrals.application.referrals_service import ReferralsService
                from app.domains.referrals.infrastructure.repositories.referrals_repository import (
                    ReferralsRepository,
                )

                svc = ReferralsService(ReferralsRepository(db))
                await svc.process_signup_referral(db, referral_code=payload.referral_code, referee_user_id=user.id)
        except Exception:
            # do not block signup on referral errors
            pass
        token = uuid4().hex
        await self._verification_store.set(token, str(user.id))
        return {"verification_token": token}

    async def verify_email(self, db: AsyncSession, token: str) -> dict[str, Any]:
        user_id = await self._verification_store.pop(token)
        if not user_id:
            raise http_error(400, "Invalid token")
        q = await db.execute(select(User).where(User.id == user_id))
        user = q.scalars().first()
        if not user:
            raise http_error(400, "Invalid token")
        user.is_active = True
        db.add(user)
        await db.commit()
        return {"message": "Email verified"}

    async def change_password(
        self, db: AsyncSession, token: str, old_password: str, new_password: str
    ) -> dict[str, Any]:
        user_id = self._tokens.verify_access_token(token)
        if not user_id:
            raise http_error(401, "Invalid token")
        q = await db.execute(select(User).where(User.id == user_id))
        user = q.scalars().first()
        if not user or not verify_password(old_password, user.password_hash or ""):
            raise http_error(400, "Incorrect old password")
        user.password_hash = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        return {"message": "Password updated"}

    async def logout(self) -> dict[str, Any]:
        return {"message": "Logged out"}

    async def evm_nonce(self, user_id: str) -> dict[str, str]:
        nonce = uuid4().hex
        await self._nonce_store.set(user_id, nonce)
        return {"nonce": nonce}

    async def evm_verify(self, payload: EVMVerify) -> dict[str, Any]:
        stored = await self._nonce_store.pop(payload.wallet_address)
        if not stored or stored != payload.message:
            raise http_error(400, "Invalid nonce")
        return {"message": "Wallet verified"}
