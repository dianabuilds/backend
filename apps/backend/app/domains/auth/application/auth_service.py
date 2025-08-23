from __future__ import annotations

from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from uuid import uuid4

from app.domains.auth.application.ports.token_port import ITokenService
from app.domains.users.infrastructure.models.user import User
from app.schemas.auth import LoginSchema, LoginResponse, Token, SignupSchema
from app.core.security import verify_password, get_password_hash


class AuthService:
    def __init__(self, tokens: ITokenService) -> None:
        self._tokens = tokens
        self._verification_tokens: dict[str, str] = {}

    async def login(self, db: AsyncSession, payload: LoginSchema) -> LoginResponse:
        # Простая аутентификация по email/username и паролю
        q = await db.execute(
            select(User).where(
                (User.email == payload.login) | (User.username == payload.login)
            )
        )
        user = q.scalars().first()
        if not user or not verify_password(payload.password, user.password_hash or ""):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Incorrect username or password",
                    }
                },
            )
        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Email not verified",
                    }
                },
            )
        access = self._tokens.create_access_token(str(user.id))
        refresh = self._tokens.create_refresh_token(str(user.id))
        return LoginResponse(
            access_token=access, refresh_token=refresh, token_type="bearer"
        )

    async def refresh(self, payload: Token) -> LoginResponse:
        sub = self._tokens.verify_access_token(payload.token)
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        # В данной модели ре‑логинимся по subject
        access = self._tokens.create_access_token(sub)
        refresh = self._tokens.create_refresh_token(sub)
        return LoginResponse(
            access_token=access, refresh_token=refresh, token_type="bearer"
        )

    async def signup(
        self, db: AsyncSession, payload: SignupSchema, mailer: object
    ) -> dict:
        # Check for duplicate username
        q = await db.execute(select(User).where(User.username == payload.username))
        if q.scalars().first():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Username already taken",
                    }
                },
            )
        # Check for duplicate email
        q = await db.execute(select(User).where(User.email == payload.email))
        if q.scalars().first():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Email already registered",
                    }
                },
            )
        user = User(
            email=payload.email,
            username=payload.username,
            password_hash=get_password_hash(payload.password),
            is_active=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = uuid4().hex
        self._verification_tokens[token] = str(user.id)
        return {"verification_token": token}

    async def verify_email(self, db: AsyncSession, token: str) -> dict:
        user_id = self._verification_tokens.pop(token, None)
        if not user_id:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "BAD_REQUEST", "message": "Invalid token"}},
            )
        q = await db.execute(select(User).where(User.id == user_id))
        user = q.scalars().first()
        if not user:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "BAD_REQUEST", "message": "Invalid token"}},
            )
        user.is_active = True
        db.add(user)
        await db.commit()
        return {"message": "Email verified"}

    async def change_password(
        self, db: AsyncSession, token: str, old_password: str, new_password: str
    ) -> dict:
        user_id = self._tokens.verify_access_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        q = await db.execute(select(User).where(User.id == user_id))
        user = q.scalars().first()
        if not user or not verify_password(old_password, user.password_hash or ""):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "Incorrect old password",
                    }
                },
            )
        user.password_hash = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        return {"message": "Password updated"}
