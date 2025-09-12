from __future__ import annotations

from typing import Protocol
from uuid import UUID
from zoneinfo import ZoneInfo


class _Repo(Protocol):
    async def get_display(self, user_id: UUID) -> dict | None:  # pragma: no cover - contract
        ...

    async def update_fields(self, user_id: UUID, data: dict) -> dict:  # pragma: no cover - contract
        ...


class ProfileService:
    def __init__(self, repo: _Repo) -> None:
        self._repo = repo

    def _validate_timezone(self, tz: str | None) -> None:
        if tz:
            try:
                ZoneInfo(tz)
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError("Invalid timezone") from exc

    def _validate_locale(self, locale: str | None) -> None:
        if locale and len(locale) > 10:
            raise ValueError("Invalid locale")

    async def get(self, user_id: UUID) -> dict | None:
        return await self._repo.get_display(user_id)

    async def update(self, user_id: UUID, data: dict) -> dict:
        # Validate display-level fields if present
        if "lang" in data:
            self._validate_locale(data.get("lang"))
        return await self._repo.update_fields(user_id, data)

    async def get_settings(self, user_id: UUID) -> dict:
        # type: ignore[attr-defined]
        return await self._repo.get_settings(user_id)

    async def update_settings(self, user_id: UUID, prefs: dict) -> dict:
        # type: ignore[attr-defined]
        return await self._repo.update_settings(user_id, prefs)

    async def get_profile_fields(self, user_id: UUID) -> dict:
        # type: ignore[attr-defined]
        return await self._repo.get_profile_fields(user_id)

    async def update_profile_fields(self, user_id: UUID, data: dict) -> dict:
        # Optional validation for profile fields used by legacy routes
        self._validate_timezone(data.get("timezone"))
        self._validate_locale(data.get("locale"))
        # type: ignore[attr-defined]
        return await self._repo.update_profile_fields(user_id, data)

__all__ = ["ProfileService"]
