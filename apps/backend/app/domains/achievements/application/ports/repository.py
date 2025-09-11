from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domains.achievements.infrastructure.models.achievement_models import (
    Achievement,
    UserAchievement,
)


class IAchievementsRepository(Protocol):
    async def user_has_achievement(
        self, user_id: UUID, achievement_id: UUID
    ) -> bool:  # pragma: no cover
        ...

    async def get_achievement(self, achievement_id: UUID) -> Achievement | None:  # pragma: no cover
        ...

    async def add_user_achievement(
        self, user_id: UUID, achievement_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def delete_user_achievement(
        self, user_id: UUID, achievement_id: UUID
    ) -> bool:  # pragma: no cover
        ...

    async def list_user_achievements(
        self, user_id: UUID
    ) -> list[tuple[Achievement, UserAchievement | None]]:  # pragma: no cover
        ...

    async def increment_counter(self, user_id: UUID, key: str) -> None:  # pragma: no cover
        ...

    async def get_counter(self, user_id: UUID, key: str) -> int:  # pragma: no cover
        ...

    async def list_locked_achievements(
        self, user_id: UUID
    ) -> list[Achievement]:  # pragma: no cover
        ...

    async def is_user_premium(self, user_id: UUID) -> bool:  # pragma: no cover
        ...

    async def count_nodes_by_author(self, user_id: UUID) -> int:  # pragma: no cover
        ...

    async def sum_views_by_author(self, user_id: UUID) -> int:  # pragma: no cover
        ...

    async def list_achievements(self) -> list[Achievement]:  # pragma: no cover
        ...

    async def exists_code(self, code: str) -> bool:  # pragma: no cover
        ...

    async def create_achievement(
        self, data: dict[str, Any], actor_id: UUID
    ) -> Achievement:  # pragma: no cover
        ...

    async def update_achievement_fields(
        self, item: Achievement, data: dict[str, Any], actor_id: UUID
    ) -> Achievement:  # pragma: no cover
        ...

    async def delete_achievement(self, item: Achievement) -> None:  # pragma: no cover
        ...
