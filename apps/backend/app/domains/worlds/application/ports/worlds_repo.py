from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.domains.ai.infrastructure.models.world_models import Character, WorldTemplate


class IWorldsRepository(Protocol):
    async def list_worlds(self, profile_id: UUID) -> list[WorldTemplate]:  # pragma: no cover
        ...

    async def get_world(
        self, world_id: UUID, profile_id: UUID
    ) -> WorldTemplate | None:  # pragma: no cover
        ...

    async def create_world(
        self, profile_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> WorldTemplate:  # pragma: no cover
        ...

    async def update_world(
        self,
        world: WorldTemplate,
        data: dict[str, Any],
        profile_id: UUID,
        actor_id: UUID,
    ) -> WorldTemplate:  # pragma: no cover
        ...

    async def delete_world(
        self, world: WorldTemplate, profile_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def list_characters(
        self, world_id: UUID, profile_id: UUID
    ) -> list[Character]:  # pragma: no cover
        ...

    async def create_character(
        self, world_id: UUID, profile_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> Character:  # pragma: no cover
        ...

    async def update_character(
        self,
        character: Character,
        data: dict[str, Any],
        profile_id: UUID,
        actor_id: UUID,
    ) -> Character:  # pragma: no cover
        ...

    async def delete_character(
        self, character: Character, profile_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def get_character(
        self, char_id: UUID, profile_id: UUID
    ) -> Character | None:  # pragma: no cover
        ...
