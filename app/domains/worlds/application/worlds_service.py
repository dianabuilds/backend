from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.worlds.application.ports.worlds_repo import IWorldsRepository
from app.domains.ai.infrastructure.models.world_models import WorldTemplate, Character


class WorldsService:
    def __init__(self, repo: IWorldsRepository) -> None:
        self._repo = repo

    async def list_worlds(self) -> List[WorldTemplate]:
        return await self._repo.list_worlds()

    async def create_world(self, db: AsyncSession, data: dict[str, Any]) -> WorldTemplate:
        world = await self._repo.create_world(data)
        await db.commit()
        return world

    async def update_world(self, db: AsyncSession, world_id: UUID, data: dict[str, Any]) -> Optional[WorldTemplate]:
        world = await self._repo.get_world(world_id)
        if not world:
            return None
        updated = await self._repo.update_world(world, data)
        await db.commit()
        return updated

    async def delete_world(self, db: AsyncSession, world_id: UUID) -> bool:
        world = await self._repo.get_world(world_id)
        if not world:
            return False
        await self._repo.delete_world(world)
        await db.commit()
        return True

    async def list_characters(self, world_id: UUID) -> List[Character]:
        return await self._repo.list_characters(world_id)

    async def create_character(self, db: AsyncSession, world_id: UUID, data: dict[str, Any]) -> Optional[Character]:
        world = await self._repo.get_world(world_id)
        if not world:
            return None
        ch = await self._repo.create_character(world_id, data)
        await db.commit()
        return ch

    async def update_character(self, db: AsyncSession, char_id: UUID, data: dict[str, Any]) -> Optional[Character]:
        ch = await self._repo.get_character(char_id)
        if not ch:
            return None
        ch = await self._repo.update_character(ch, data)
        await db.commit()
        return ch

    async def delete_character(self, db: AsyncSession, char_id: UUID) -> bool:
        ch = await self._repo.get_character(char_id)
        if not ch:
            return False
        await self._repo.delete_character(ch)
        await db.commit()
        return True
