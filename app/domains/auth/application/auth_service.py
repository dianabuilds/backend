from __future__ import annotations

from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.domains.auth.application.ports.token_port import ITokenService
from app.domains.users.infrastructure.models.user import User
from app.schemas.auth import LoginSchema, LoginResponse, Token
from app.core.security import verify_password


class AuthService:
    def __init__(self, tokens: ITokenService) -> None:
        self._tokens = tokens

    async def login(self, db: AsyncSession, payload: LoginSchema) -> LoginResponse:
        # Простая аутентификация по email/username и паролю
        q = await db.execute(select(User).where((User.email == payload.login) | (User.username == payload.login)))
        user = q.scalars().first()
        if not user or not verify_password(payload.password, user.password_hash or ""):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access = self._tokens.create_access_token(str(user.id))
        refresh = self._tokens.create_refresh_token(str(user.id))
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    async def refresh(self, payload: Token) -> LoginResponse:
        sub = self._tokens.verify_access_token(payload.token)
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        # В данной модели ре‑логинимся по subject
        access = self._tokens.create_access_token(sub)
        refresh = self._tokens.create_refresh_token(sub)
        return LoginResponse(access_token=access, refresh_token=refresh, token_type="bearer")
