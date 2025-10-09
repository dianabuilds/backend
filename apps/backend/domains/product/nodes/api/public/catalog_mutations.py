from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from domains.platform.iam.security import csrf_protect, get_current_user

from .deps import get_catalog_mutations_service


def register_catalog_mutation_routes(router: APIRouter) -> None:
    service_dep = Depends(get_catalog_mutations_service)

    @router.put("/{node_id}/tags")
    async def set_tags(
        node_id: str,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        tags = body.get("tags") or []
        if not isinstance(tags, list):
            raise HTTPException(status_code=400, detail="tags_list_required")
        return await service.set_tags(node_id, tags, claims)

    @router.post("")
    async def create_node(
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        title = body.get("title")
        if title is not None and not isinstance(title, str):
            raise HTTPException(status_code=400, detail="title_invalid")
        tags = body.get("tags") or []
        if not isinstance(tags, list):
            raise HTTPException(status_code=400, detail="tags_list_required")
        is_public = body.get("is_public")
        if is_public is not None and not isinstance(is_public, bool):
            raise HTTPException(status_code=400, detail="is_public_invalid")
        return await service.create(body, claims)

    @router.patch("/{node_id}")
    async def patch_node(
        node_id: str,
        body: dict[str, Any],
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        title = body.get("title")
        if title is not None and not isinstance(title, str):
            raise HTTPException(status_code=400, detail="title_invalid")
        is_public = body.get("is_public")
        if is_public is not None and not isinstance(is_public, bool):
            raise HTTPException(status_code=400, detail="is_public_invalid")
        status = body.get("status")
        if status is not None and not isinstance(status, str):
            raise HTTPException(status_code=400, detail="status_invalid")
        return await service.update(node_id, body, claims)

    @router.delete("/{node_id}")
    async def delete_node(
        node_id: str,
        _req: Request,
        service=service_dep,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        return await service.delete(node_id, claims)
