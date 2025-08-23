from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from app.domains.ai.infrastructure.models.world_models import Character, WorldTemplate


class IWorldsRepository:
    async def list_worlds(
        self, workspace_id: UUID
    ) -> List[WorldTemplate]:  # pragma: no cover
        ...

    async def get_world(
        self, world_id: UUID, workspace_id: UUID
    ) -> Optional[WorldTemplate]:  # pragma: no cover
        ...

    async def create_world(
        self, workspace_id: UUID, data: dict[str, Any]
    ) -> WorldTemplate:  # pragma: no cover
        ...

    async def update_world(
        self, world: WorldTemplate, data: dict[str, Any], workspace_id: UUID
    ) -> WorldTemplate:  # pragma: no cover
        ...

    async def delete_world(
        self, world: WorldTemplate, workspace_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def list_characters(
        self, world_id: UUID, workspace_id: UUID
    ) -> List[Character]:  # pragma: no cover
        ...

    async def create_character(
        self, world_id: UUID, workspace_id: UUID, data: dict[str, Any]
    ) -> Character:  # pragma: no cover
        ...

    async def update_character(
        self, character: Character, data: dict[str, Any], workspace_id: UUID
    ) -> Character:  # pragma: no cover
        ...

    async def delete_character(
        self, character: Character, workspace_id: UUID
    ) -> None:  # pragma: no cover
        ...

    async def get_character(
        self, char_id: UUID, workspace_id: UUID
    ) -> Optional[Character]:  # pragma: no cover
        ...
