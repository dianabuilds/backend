from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel.errors import http_error
from app.domains.auth.application.ports.hasher import IPasswordHasher
from app.domains.auth.application.ports.user_repo import IUserRepository
from app.domains.auth.application.ports.tokens import ITokenService
from app.domains.auth.infrastructure.nonce_store import NonceStore
from app.domains.auth.infrastructure.verification_token_store import (
    VerificationTokenStore,
)
from app.domains.auth.infrastructure.password_reset_store import PasswordResetStore
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
        reset_store: PasswordResetStore | None = None,
        hasher: IPasswordHasher | None = None,
    ) -> None:
        self._tokens = tokens
        self._verification_store = verification_store
        self._nonce_store = nonce_store
        self._reset_store = reset_store
        self._hasher = hasher

    async def login(self, db: AsyncSession, payload: LoginSchema, repo: IUserRepository) -> LoginResponse:
        user = await repo.get_by_email(payload.login)
        if user is None:
            user = await repo.get_by_username(payload.login)
        hasher = self._hasher
        if not user or not (hasher and hasher.verify(payload.password, user.password_hash or "")):
            raise http_error(400, "Incorrect username or password")
        if not user.is_active:
            raise http_error(400, "Email not verified")
        await repo.update_last_login(user, datetime.utcnow())
        await db.commit()
        access = self._tokens.create_access_token(str(user.id))
        refresh = await self._tokens.create_refresh_token(str(user.id))
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    async def refresh(self, payload: Token) -> LoginResponse:
        sub = await self._tokens.verify_refresh_token(payload.token)
        if not sub:
            raise http_error(401, "Invalid refresh token")
        access = self._tokens.create_access_token(sub)
        refresh = await self._tokens.create_refresh_token(sub)
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    async def signup(
        self, db: AsyncSession, payload: SignupSchema, mailer: object, repo: IUserRepository
    ) -> dict[str, Any]:
        existing = await repo.get_by_username(payload.username)
        if existing:
            raise http_error(400, "Username already taken")
        if await repo.get_by_email(payload.email):
            raise http_error(400, "Email already registered")
        hasher = self._hasher
        user = await repo.create(
            email=payload.email,
            password_hash=(hasher.hash(payload.password) if hasher else payload.password),
            is_active=False,
        )
        user.username = payload.username
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
                await svc.process_signup_referral(
                    db, referral_code=payload.referral_code, referee_user_id=user.id
                )
        except Exception:
            # do not block signup on referral errors
            pass
        token = uuid4().hex
        await self._verification_store.set(token, str(user.id))
        return {"verification_token": token}

    async def verify_email(self, db: AsyncSession, token: str, repo: IUserRepository) -> dict[str, Any]:
        user_id = await self._verification_store.pop(token)
        if not user_id:
            raise http_error(400, "Invalid token")
        user = await repo.get_by_id(user_id)
        if not user:
            raise http_error(400, "Invalid token")
        await repo.set_active(user, True)
        await db.commit()
        return {"message": "Email verified"}

    async def change_password(
        self, db: AsyncSession, token: str, old_password: str, new_password: str, repo: IUserRepository
    ) -> dict[str, Any]:
        user_id = self._tokens.verify_access_token(token)
        if not user_id:
            raise http_error(401, "Invalid token")
        user = await repo.get_by_id(user_id)
        hasher = self._hasher
        if not user or not (hasher and hasher.verify(old_password, user.password_hash or "")):
            raise http_error(400, "Incorrect old password")
        await repo.set_password(user, hasher.hash(new_password) if hasher else new_password)
        await db.commit()
        return {"message": "Password updated"}

    async def logout(self) -> dict[str, Any]:
        return {"message": "Logged out"}

    async def request_password_reset(
        self, db: AsyncSession, email: str, mailer: object, repo: IUserRepository
    ) -> dict[str, Any]:
        user = await repo.get_by_email(email)
        # Do not leak existence; send if exists
        if user and self._reset_store is not None:
            token = uuid4().hex
            await self._reset_store.set(token, str(user.id))
            try:
                # IMailer expected
                await mailer.send_reset_password(email, token)  # type: ignore[attr-defined]
            except Exception:
                pass
        await db.commit()
        return {"message": "If the email is registered, a reset link was sent"}

    async def confirm_password_reset(
        self, db: AsyncSession, token: str, new_password: str, repo: IUserRepository
    ) -> dict[str, Any]:
        if self._reset_store is None:
            raise http_error(500, "Password reset not available")
        user_id = await self._reset_store.pop(token)
        if not user_id:
            raise http_error(400, "Invalid token")
        user = await repo.get_by_id(user_id)
        if not user:
            raise http_error(400, "Invalid token")
        hasher = self._hasher
        await repo.set_password(user, hasher.hash(new_password) if hasher else new_password)
        await db.commit()
        return {"message": "Password updated"}

    async def evm_nonce(self, user_id: str) -> dict[str, str]:
        nonce = uuid4().hex
        await self._nonce_store.set(user_id, nonce)
        return {"nonce": nonce}

    async def evm_verify(self, payload: EVMVerify) -> dict[str, Any]:
        stored = await self._nonce_store.pop(payload.wallet_address)
        if not stored or stored != payload.message:
            raise http_error(400, "Invalid nonce")
        return {"message": "Wallet verified"}
