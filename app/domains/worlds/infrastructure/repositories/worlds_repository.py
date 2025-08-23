from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.worlds.application.ports.worlds_repo import IWorldsRepository
from app.domains.ai.infrastructure.models.world_models import Character, WorldTemplate


class WorldsRepository(IWorldsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_worlds(self, workspace_id: UUID) -> List[WorldTemplate]:
        res = await self._db.execute(
            select(WorldTemplate)
            .where(WorldTemplate.workspace_id == workspace_id)
            .order_by(WorldTemplate.created_at.desc())
        )
        return list(res.scalars().all())

    async def get_world(
        self, world_id: UUID, workspace_id: UUID
    ) -> Optional[WorldTemplate]:
        res = await self._db.execute(
            select(WorldTemplate).where(
                WorldTemplate.id == world_id, WorldTemplate.workspace_id == workspace_id
            )
        )
        return res.scalar_one_or_none()

    async def create_world(
        self, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> WorldTemplate:
        world = WorldTemplate(
            workspace_id=workspace_id, created_by_user_id=actor_id, **data
        )
        self._db.add(world)
        await self._db.flush()
        await self._db.refresh(world)
        return world

    async def update_world(
        self, world: WorldTemplate, data: dict[str, Any], workspace_id: UUID, actor_id: UUID
    ) -> WorldTemplate:
        if world.workspace_id != workspace_id:
            return world
        for k, v in (data or {}).items():
            setattr(world, k, v)
        world.updated_by_user_id = actor_id
        await self._db.flush()
        await self._db.refresh(world)
        return world

    async def delete_world(self, world: WorldTemplate, workspace_id: UUID) -> None:
        if world.workspace_id != workspace_id:
            return
        await self._db.delete(world)
        await self._db.flush()

    async def list_characters(
        self, world_id: UUID, workspace_id: UUID
    ) -> List[Character]:
        res = await self._db.execute(
            select(Character)
            .where(
                Character.world_id == world_id,
                Character.workspace_id == workspace_id,
            )
            .order_by(Character.created_at.asc())
        )
        return list(res.scalars().all())

    async def create_character(
        self, world_id: UUID, workspace_id: UUID, data: dict[str, Any], actor_id: UUID
    ) -> Character:
        ch = Character(
            world_id=world_id,
            workspace_id=workspace_id,
            created_by_user_id=actor_id,
            **data,
        )
        self._db.add(ch)
        await self._db.flush()
        await self._db.refresh(ch)
        return ch

    async def update_character(
        self, character: Character, data: dict[str, Any], workspace_id: UUID, actor_id: UUID
    ) -> Character:
        if character.workspace_id != workspace_id:
            return character
        for k, v in (data or {}).items():
            setattr(character, k, v)
        character.updated_by_user_id = actor_id
        await self._db.flush()
        await self._db.refresh(character)
        return character

    async def delete_character(self, character: Character, workspace_id: UUID) -> None:
        if character.workspace_id != workspace_id:
            return
        await self._db.delete(character)
        await self._db.flush()

    async def get_character(
        self, char_id: UUID, workspace_id: UUID
    ) -> Optional[Character]:
        res = await self._db.execute(
            select(Character).where(
                Character.id == char_id, Character.workspace_id == workspace_id
            )
        )
        return res.scalar_one_or_none()
