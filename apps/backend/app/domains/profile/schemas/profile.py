from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ProfileOut(BaseModel):
    id: UUID
    userId: UUID
    username: str | None = None
    avatar: str | None = None
    bio: str | None = None
    lang: str | None = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    username: str | None = None
    avatar: str | None = None
    bio: str | None = None
    lang: str | None = None


class ProfileSettingsOut(BaseModel):
    preferences: dict

    model_config = {"from_attributes": True}


class ProfileSettingsUpdate(BaseModel):
    preferences: dict


__all__ = [
    "ProfileOut",
    "ProfileUpdate",
    "ProfileSettingsOut",
    "ProfileSettingsUpdate",
]

