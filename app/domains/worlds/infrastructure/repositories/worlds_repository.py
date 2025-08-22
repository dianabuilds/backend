from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.worlds.application.ports.worlds_repo import IWorldsRepository
from app.domains.ai.infrastructure.models.world_models import WorldTemplate, Character


class WorldsRepository(IWorldsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_worlds(self) -> List[WorldTemplate]:
        res = await self._db.execute(select(WorldTemplate).order_by(WorldTemplate.created_at.desc()))
        return list(res.scalars().all())

    async def get_world(self, world_id: UUID) -> Optional[WorldTemplate]:
        return await self._db.get(WorldTemplate, world_id)

    async def create_world(self, data: dict[str, Any]) -> WorldTemplate:
        world = WorldTemplate(**data)
        self._db.add(world)
        await self._db.flush()
        await self._db.refresh(world)
        return world

    async def update_world(self, world: WorldTemplate, data: dict[str, Any]) -> WorldTemplate:
        for k, v in (data or {}).items():
            setattr(world, k, v)
        await self._db.flush()
        await self._db.refresh(world)
        return world

    async def delete_world(self, world: WorldTemplate) -> None:
        await self._db.delete(world)
        await self._db.flush()

    async def list_characters(self, world_id: UUID) -> List[Character]:
        res = await self._db.execute(select(Character).where(Character.world_id == world_id).order_by(Character.created_at.asc()))
        return list(res.scalars().all())

    async def create_character(self, world_id: UUID, data: dict[str, Any]) -> Character:
        ch = Character(world_id=world_id, **data)
        self._db.add(ch)
        await self._db.flush()
        await self._db.refresh(ch)
        return ch

    async def update_character(self, character: Character, data: dict[str, Any]) -> Character:
        for k, v in (data or {}).items():
            setattr(character, k, v)
        await self._db.flush()
        await self._db.refresh(character)
        return character

    async def delete_character(self, character: Character) -> None:
        await self._db.delete(character)
        await self._db.flush()

    async def get_character(self, char_id: UUID) -> Optional[Character]:
        return await self._db.get(Character, char_id)
