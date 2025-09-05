from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domains.achievements.infrastructure.models.achievement_models import (
    Achievement,
    UserAchievement,
)


class IAchievementsRepository(Protocol):
    # User achievements
    async def user_has_achievement(
        self, user_id: UUID, achievement_id: UUID, workspace_id: UUID
    ) -> bool:  # pragma: no cover
        ...

    async def get_achievement(
        self, achievement_id: UUID, workspace_id: UUID
    ) -> Achievement | None:  # pragma: no cover
        ...

    async def add_user_achievement(
        self, user_id: UUID, achievement_id: UUID, workspace_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def delete_user_achievement(
        self, user_id: UUID, achievement_id: UUID, workspace_id: UUID
    ) -> bool:  # pragma: no cover
        ...

    async def list_user_achievements(
        self, user_id: UUID, workspace_id: UUID
    ) -> list[tuple[Achievement, UserAchievement | None]]:  # pragma: no cover
        ...

    # Counters/conditions
    async def increment_counter(
        self, user_id: UUID, key: str, workspace_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def get_counter(
        self, user_id: UUID, key: str, workspace_id: UUID
    ) -> int:  # pragma: no cover
        ...

    async def list_locked_achievements(
        self, user_id: UUID, workspace_id: UUID
    ) -> list[Achievement]:  # pragma: no cover
        ...

    async def is_user_premium(self, user_id: UUID) -> bool:  # pragma: no cover
        ...

    async def count_nodes_by_author(
        self, user_id: UUID, workspace_id: UUID
    ) -> int:  # pragma: no cover
        ...

    async def sum_views_by_author(
        self, user_id: UUID, workspace_id: UUID
    ) -> int:  # pragma: no cover
        ...

    # CRUD for achievements (admin)
    async def list_achievements(self, workspace_id: UUID) -> list[Achievement]:  # pragma: no cover
        ...

    async def exists_code(self, code: str, workspace_id: UUID) -> bool:  # pragma: no cover
        ...

    async def create_achievement(
        self, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> Achievement:  # pragma: no cover
        ...

    async def update_achievement_fields(
        self,
        item: Achievement,
        data: dict[str, Any],
        workspace_id: UUID,
        actor_id: UUID,
    ) -> Achievement:  # pragma: no cover
        ...

    async def delete_achievement(
        self, item: Achievement, workspace_id: UUID
    ) -> None:  # pragma: no cover
        ...
