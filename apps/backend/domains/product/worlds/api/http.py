from __future__ import annotations

from uuid import UUID

import anyio
from fastapi import APIRouter, Depends, HTTPException

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_role_db,
)
from domains.product.worlds.api.schemas import (
    CharacterIn,
    CharacterOut,
    CharacterPatch,
    WorldTemplateIn,
    WorldTemplateOut,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin/worlds", tags=["admin-worlds"])
    admin_required = require_role_db("moderator")  # moderator+ allowed

    @router.get(
        "", response_model=list[WorldTemplateOut], summary="List world templates"
    )
    async def list_worlds(
        _: None = Depends(admin_required),
        container=Depends(get_container),
    ):
        items = await anyio.to_thread.run_sync(container.worlds_service.list_worlds)
        return [
            WorldTemplateOut(
                id=UUID(w.id),
                title=w.title,
                locale=w.locale,
                description=w.description,
                meta=w.meta,
                created_at=w.created_at,
                updated_at=w.updated_at,
                created_by_user_id=(
                    UUID(w.created_by_user_id) if w.created_by_user_id else None
                ),
                updated_by_user_id=(
                    UUID(w.updated_by_user_id) if w.updated_by_user_id else None
                ),
            )
            for w in items
        ]

    @router.get(
        "/{world_id}", response_model=WorldTemplateOut, summary="Get world template"
    )
    async def get_world(
        world_id: UUID,
        _: None = Depends(admin_required),
        container=Depends(get_container),
    ):
        w = await anyio.to_thread.run_sync(
            container.worlds_service.get_world, str(world_id)
        )
        if not w:
            raise HTTPException(status_code=404, detail="not_found")
        return WorldTemplateOut(
            id=UUID(w.id),
            title=w.title,
            locale=w.locale,
            description=w.description,
            meta=w.meta,
            created_at=w.created_at,
            updated_at=w.updated_at,
            created_by_user_id=(
                UUID(w.created_by_user_id) if w.created_by_user_id else None
            ),
            updated_by_user_id=(
                UUID(w.updated_by_user_id) if w.updated_by_user_id else None
            ),
        )

    @router.post("", response_model=WorldTemplateOut, summary="Create world template")
    async def create_world(
        payload: WorldTemplateIn,
        _: None = Depends(admin_required),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        actor = str(claims.get("sub") or "")
        w = await anyio.to_thread.run_sync(
            container.worlds_service.create_world,
            payload.model_dump(exclude_none=True),
            actor,
        )
        return WorldTemplateOut(
            id=UUID(w.id),
            title=w.title,
            locale=w.locale,
            description=w.description,
            meta=w.meta,
            created_at=w.created_at,
            updated_at=w.updated_at,
            created_by_user_id=(
                UUID(w.created_by_user_id) if w.created_by_user_id else None
            ),
            updated_by_user_id=(
                UUID(w.updated_by_user_id) if w.updated_by_user_id else None
            ),
        )

    @router.patch(
        "/{world_id}", response_model=WorldTemplateOut, summary="Update world template"
    )
    async def update_world(
        world_id: UUID,
        payload: WorldTemplateIn,
        _: None = Depends(admin_required),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        actor = str(claims.get("sub") or "")
        out = await anyio.to_thread.run_sync(
            container.worlds_service.update_world,
            str(world_id),
            payload.model_dump(exclude_none=True),
            actor,
        )
        if not out:
            raise HTTPException(status_code=404, detail="not_found")
        return WorldTemplateOut(
            id=UUID(out.id),
            title=out.title,
            locale=out.locale,
            description=out.description,
            meta=out.meta,
            created_at=out.created_at,
            updated_at=out.updated_at,
            created_by_user_id=(
                UUID(out.created_by_user_id) if out.created_by_user_id else None
            ),
            updated_by_user_id=(
                UUID(out.updated_by_user_id) if out.updated_by_user_id else None
            ),
        )

    @router.delete("/{world_id}", summary="Delete world template")
    async def delete_world(
        world_id: UUID,
        _: None = Depends(admin_required),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        ok = await anyio.to_thread.run_sync(
            container.worlds_service.delete_world, str(world_id)
        )
        if not ok:
            raise HTTPException(status_code=404, detail="not_found")
        return {"status": "ok"}

    @router.get(
        "/characters/{char_id}", response_model=CharacterOut, summary="Get character"
    )
    async def get_character(
        char_id: UUID,
        _: None = Depends(admin_required),
        container=Depends(get_container),
    ):
        ch = await anyio.to_thread.run_sync(
            container.worlds_service.get_character, str(char_id)
        )
        if not ch:
            raise HTTPException(status_code=404, detail="not_found")
        return CharacterOut(
            id=UUID(ch.id),
            world_id=UUID(ch.world_id),
            name=ch.name,
            role=ch.role,
            description=ch.description,
            traits=ch.traits,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
            created_by_user_id=(
                UUID(ch.created_by_user_id) if ch.created_by_user_id else None
            ),
            updated_by_user_id=(
                UUID(ch.updated_by_user_id) if ch.updated_by_user_id else None
            ),
        )

    @router.get(
        "/{world_id}/characters",
        response_model=list[CharacterOut],
        summary="List characters",
    )
    async def list_characters(
        world_id: UUID,
        _: None = Depends(admin_required),
        container=Depends(get_container),
    ):
        chs = await anyio.to_thread.run_sync(
            container.worlds_service.list_characters,
            str(world_id),
        )
        return [
            CharacterOut(
                id=UUID(c.id),
                world_id=UUID(c.world_id),
                name=c.name,
                role=c.role,
                description=c.description,
                traits=c.traits,
                created_at=c.created_at,
                updated_at=c.updated_at,
                created_by_user_id=(
                    UUID(c.created_by_user_id) if c.created_by_user_id else None
                ),
                updated_by_user_id=(
                    UUID(c.updated_by_user_id) if c.updated_by_user_id else None
                ),
            )
            for c in chs
        ]

    @router.post(
        "/{world_id}/characters",
        response_model=CharacterOut,
        summary="Create character",
    )
    async def create_character(
        world_id: UUID,
        payload: CharacterIn,
        _: None = Depends(admin_required),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        actor = str(claims.get("sub") or "")
        ch = await anyio.to_thread.run_sync(
            container.worlds_service.create_character,
            str(world_id),
            payload.model_dump(exclude_none=True),
            actor,
        )
        if not ch:
            raise HTTPException(status_code=404, detail="world_not_found")
        return CharacterOut(
            id=UUID(ch.id),
            world_id=UUID(ch.world_id),
            name=ch.name,
            role=ch.role,
            description=ch.description,
            traits=ch.traits,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
            created_by_user_id=(
                UUID(ch.created_by_user_id) if ch.created_by_user_id else None
            ),
            updated_by_user_id=(
                UUID(ch.updated_by_user_id) if ch.updated_by_user_id else None
            ),
        )

    @router.patch(
        "/characters/{char_id}",
        response_model=CharacterOut,
        summary="Update character",
    )
    async def update_character(
        char_id: UUID,
        payload: CharacterPatch,
        _: None = Depends(admin_required),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        actor = str(claims.get("sub") or "")
        ch = await anyio.to_thread.run_sync(
            container.worlds_service.update_character,
            str(char_id),
            payload.model_dump(exclude_none=True),
            actor,
        )
        if not ch:
            raise HTTPException(status_code=404, detail="not_found")
        return CharacterOut(
            id=UUID(ch.id),
            world_id=UUID(ch.world_id),
            name=ch.name,
            role=ch.role,
            description=ch.description,
            traits=ch.traits,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
            created_by_user_id=(
                UUID(ch.created_by_user_id) if ch.created_by_user_id else None
            ),
            updated_by_user_id=(
                UUID(ch.updated_by_user_id) if ch.updated_by_user_id else None
            ),
        )

    @router.delete("/characters/{char_id}", summary="Delete character")
    async def delete_character(
        char_id: UUID,
        _: None = Depends(admin_required),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        ok = await anyio.to_thread.run_sync(
            container.worlds_service.delete_character,
            str(char_id),
        )
        if not ok:
            raise HTTPException(status_code=404, detail="not_found")
        return {"status": "ok"}

    return router
