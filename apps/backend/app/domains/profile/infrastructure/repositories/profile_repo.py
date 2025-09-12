from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.models.user_profile import UserProfile


class ProfileRepository:
    """SQLAlchemy-backed repository using existing users tables.

    Представление профиля собирается из `users` и `user_profiles`.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _ensure_profile(self, user_id: UUID) -> UserProfile:
        profile = await self._db.get(UserProfile, user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)  # type: ignore[call-arg]
            self._db.add(profile)
            await self._db.flush()
        return profile

    async def get_display(self, user_id: UUID) -> dict | None:  # type: ignore[override]
        user = await self._db.get(User, user_id)
        if user is None:
            return None
        profile = await self._db.get(UserProfile, user_id)
        return {
            "id": user.id,
            "userId": user.id,
            "username": user.username,
            "avatar": user.avatar_url,
            "bio": user.bio,
            "lang": (profile.locale if profile else None),
        }

    async def update_fields(self, user_id: UUID, data: dict) -> dict:  # type: ignore[override]
        user = await self._db.get(User, user_id)
        if user is None:
            raise ValueError("user not found")
        profile = await self._ensure_profile(user_id)

        # Map fields to tables
        username = data.get("username")
        if username is not None:
            user.username = username
        avatar = data.get("avatar")
        if avatar is not None:
            user.avatar_url = avatar
        bio = data.get("bio")
        if bio is not None:
            user.bio = bio
        lang = data.get("lang")
        if lang is not None:
            profile.locale = lang

        try:
            await self._db.flush()
        except IntegrityError as exc:  # likely username unique conflict
            # Map to a domain error the router can translate to 409
            if "username" in (data or {}):
                raise UsernameAlreadyExists() from exc
            raise
        return await self.get_display(user_id) or {}

    async def get_settings(self, user_id: UUID) -> dict:
        profile = await self._ensure_profile(user_id)
        return {"preferences": dict(profile.preferences or {})}

    async def update_settings(self, user_id: UUID, prefs: dict[str, Any]) -> dict:
        profile = await self._ensure_profile(user_id)
        current = dict(profile.preferences or {})
        current.update(prefs or {})
        profile.preferences = current
        await self._db.flush()
        return {"preferences": current}

    async def get_profile_fields(self, user_id: UUID) -> dict:
        profile = await self._ensure_profile(user_id)
        return {
            "timezone": profile.timezone,
            "locale": profile.locale,
            "links": dict(profile.links or {}),
        }

    async def update_profile_fields(self, user_id: UUID, data: dict[str, Any]) -> dict:
        profile = await self._ensure_profile(user_id)
        if "timezone" in data:
            profile.timezone = data["timezone"]
        if "locale" in data:
            profile.locale = data["locale"]
        if "links" in data and data["links"] is not None:
            links = dict(data["links"])  # shallow copy
            profile.links = links
        await self._db.flush()
        return await self.get_profile_fields(user_id)

__all__ = ["ProfileRepository"]


class UsernameAlreadyExists(Exception):
    pass
