from __future__ import annotations

from typing import Any

from packages.core.config import Settings

from .delivery.service import DeliveryService


class NotificationRetentionService:
    def __init__(
        self,
        repo: Any,
        settings: Settings,
        delivery: DeliveryService,
    ) -> None:
        self._repo = repo
        self._settings = settings
        self._delivery = delivery

    async def get_config(self) -> dict[str, Any]:
        stored = await self._repo.get_retention()
        if stored:
            return {
                "retention_days": self._coerce_optional_int(
                    stored.get("retention_days")
                ),
                "max_per_user": self._coerce_optional_int(stored.get("max_per_user")),
                "updated_at": stored.get("updated_at"),
                "updated_by": stored.get("updated_by"),
                "source": "database",
            }
        fallback_days = self._coerce_optional_int(
            getattr(self._settings.notifications, "retention_days", None)
        )
        fallback_max = self._coerce_optional_int(
            getattr(self._settings.notifications, "max_per_user", None)
        )
        return {
            "retention_days": fallback_days,
            "max_per_user": fallback_max,
            "updated_at": None,
            "updated_by": None,
            "source": "settings",
        }

    async def update_config(
        self,
        *,
        retention_days: int | None,
        max_per_user: int | None,
        actor_id: str | None,
    ) -> dict[str, Any]:
        normalized_days = self._validate_retention_days(retention_days)
        normalized_max = self._validate_max_per_user(max_per_user)
        stored = await self._repo.upsert_retention(
            retention_days=normalized_days,
            max_per_user=normalized_max,
            actor_id=actor_id,
        )
        self._delivery.update_retention(
            retention_days=normalized_days,
            max_per_user=normalized_max,
        )
        return {
            "retention_days": self._coerce_optional_int(stored.get("retention_days")),
            "max_per_user": self._coerce_optional_int(stored.get("max_per_user")),
            "updated_at": stored.get("updated_at"),
            "updated_by": stored.get("updated_by"),
            "source": "database",
        }

    async def refresh_delivery(self) -> None:
        config = await self.get_config()
        self._delivery.update_retention(
            retention_days=config.get("retention_days"),
            max_per_user=config.get("max_per_user"),
        )

    @staticmethod
    def _coerce_optional_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number

    def _validate_retention_days(self, value: int | None) -> int | None:
        normalized = self._coerce_optional_int(value)
        if normalized is None:
            return None
        if normalized <= 0:
            return None
        if normalized > 365:
            raise ValueError("retention_days must not exceed 365")
        return normalized

    def _validate_max_per_user(self, value: int | None) -> int | None:
        normalized = self._coerce_optional_int(value)
        if normalized is None:
            return None
        if normalized <= 0:
            return None
        if normalized > 1000:
            raise ValueError("max_per_user must not exceed 1000")
        return normalized


__all__ = ["NotificationRetentionService"]
