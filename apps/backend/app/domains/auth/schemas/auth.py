from __future__ import annotations

import logging
import re
from typing import Annotated

from fastapi import Request
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

logger = logging.getLogger(__name__)


class SignupSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    username: str
    referral_code: str | None = None

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._]+$", v):
            logger.warning("Invalid username format: %s", v)
            raise ValueError("Username can only contain letters, numbers, dots and underscores")
        if v in {"000", "admin", "root", "system"}:
            logger.warning("Reserved username being used: %s", v)
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_valid(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Password must be at least 3 characters long")
        if len(v) < 8 or not any(c.isupper() for c in v) or not any(c.isdigit() for c in v):
            logger.warning("Weak password being used")
        return v


class LoginSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    login: Annotated[str, Field(validation_alias=AliasChoices("login", "username", "email"))]
    password: str

    @classmethod
    async def from_request(cls, request: Request) -> "LoginSchema":
        """Получает данные логина из JSON или формы."""
        try:
            data = await request.json()
        except Exception:
            form = await request.form()
            data = {
                "login": form.get("login") or form.get("username") or form.get("email"),
                "password": form.get("password"),
            }
        return cls.model_validate(data)


class Token(BaseModel):
    token: str | None = None


class LoginResponse(BaseModel):
    ok: bool = True
    csrf_token: str | None = None
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class EVMVerify(BaseModel):
    message: str
    signature: str
    wallet_address: str

__all__ = [
    "SignupSchema",
    "LoginSchema",
    "Token",
    "LoginResponse",
    "ChangePassword",
    "EVMVerify",
]

