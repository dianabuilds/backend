from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.worlds.application.ports.worlds_repo import IWorldsRepository
from app.domains.ai.infrastructure.models.world_models import Character, WorldTemplate


class WorldsService:
    def __init__(self, repo: IWorldsRepository) -> None:
        self._repo = repo

    async def list_worlds(self, workspace_id: UUID) -> List[WorldTemplate]:
        return await self._repo.list_worlds(workspace_id)

    async def create_world(
        self, db: AsyncSession, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> WorldTemplate:
        world = await self._repo.create_world(workspace_id, data, actor_id)
        await db.commit()
        return world

    async def update_world(
        self,
        db: AsyncSession,
        workspace_id: UUID,
        world_id: UUID,
        data: dict[str, Any],
        actor_id: UUID,
    ) -> Optional[WorldTemplate]:
        world = await self._repo.get_world(world_id, workspace_id)
        if not world:
            return None
        updated = await self._repo.update_world(world, data, workspace_id, actor_id)
        await db.commit()
        return updated

    async def delete_world(
        self, db: AsyncSession, workspace_id: UUID, world_id: UUID
    ) -> bool:
        world = await self._repo.get_world(world_id, workspace_id)
        if not world:
            return False
        await self._repo.delete_world(world, workspace_id)
        await db.commit()
        return True

    async def list_characters(
        self, world_id: UUID, workspace_id: UUID
    ) -> List[Character]:
        return await self._repo.list_characters(world_id, workspace_id)

    async def create_character(
        self, db: AsyncSession, world_id: UUID, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> Optional[Character]:
        world = await self._repo.get_world(world_id, workspace_id)
        if not world:
            return None
        ch = await self._repo.create_character(world_id, workspace_id, data, actor_id)
        await db.commit()
        return ch

    async def update_character(
        self, db: AsyncSession, char_id: UUID, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> Optional[Character]:
        ch = await self._repo.get_character(char_id, workspace_id)
        if not ch:
            return None
        ch = await self._repo.update_character(ch, data, workspace_id, actor_id)
        await db.commit()
        return ch

    async def delete_character(
        self, db: AsyncSession, char_id: UUID, workspace_id: UUID
    ) -> bool:
        ch = await self._repo.get_character(char_id, workspace_id)
        if not ch:
            return False
        await self._repo.delete_character(ch, workspace_id)
        await db.commit()
        return True
