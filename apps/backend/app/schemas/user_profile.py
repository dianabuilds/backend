from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class UserProfileBase(BaseModel):
    timezone: str | None = None
    locale: str | None = None
    links: dict[str, str] = {}

    model_config = {"from_attributes": True}


class UserProfileOut(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    timezone: str | None = None
    locale: str | None = None
    links: dict[str, str] | None = None


class UserSettingsOut(BaseModel):
    preferences: dict[str, Any]

    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    preferences: dict[str, Any]
