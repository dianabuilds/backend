from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/nodes")

    @router.get("/{node_id}")
    def get_node(
        node_id: int,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        svc = container.nodes_service
        view = svc.get(node_id)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin" and not view.is_public:
            raise HTTPException(status_code=404, detail="not_found")
        return {
            "id": view.id,
            "author_id": view.author_id,
            "title": view.title,
            "tags": view.tags,
            "is_public": view.is_public,
        }

    @router.put("/{node_id}/tags")
    def set_tags(
        node_id: int,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view = svc.get(node_id)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        try:
            tags = body.get("tags") or []
            if not isinstance(tags, list):
                raise HTTPException(status_code=400, detail="tags_list_required")
            updated = svc.update_tags(node_id, tags, actor_id=uid or "")
            return {"id": updated.id, "tags": updated.tags}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @router.post("")
    async def create_node(
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub") or "") if claims else ""
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        title = body.get("title")
        if title is not None and not isinstance(title, str):
            raise HTTPException(status_code=400, detail="title_invalid")
        tags = body.get("tags") or []
        if not isinstance(tags, list):
            raise HTTPException(status_code=400, detail="tags_list_required")
        is_public = bool(body.get("is_public", False))
        svc = container.nodes_service
        view = await svc.create(
            author_id=uid, title=title, tags=tags, is_public=is_public
        )
        return {
            "id": view.id,
            "title": view.title,
            "tags": view.tags,
            "is_public": view.is_public,
        }

    @router.patch("/{node_id}")
    async def patch_node(
        node_id: int,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view = svc.get(node_id)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub") or "") if claims else ""
        role = str(claims.get("role") or "").lower()
        if view.author_id != uid and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        title = body.get("title")
        if title is not None and not isinstance(title, str):
            raise HTTPException(status_code=400, detail="title_invalid")
        is_public = body.get("is_public")
        if is_public is not None and not isinstance(is_public, bool):
            raise HTTPException(status_code=400, detail="is_public_invalid")
        updated = await container.nodes_service.update(
            node_id, title=title, is_public=is_public
        )
        return {
            "id": updated.id,
            "title": updated.title,
            "is_public": updated.is_public,
        }

    @router.delete("/{node_id}")
    async def delete_node(
        node_id: int,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.nodes_service
        view = svc.get(node_id)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub") or "") if claims else ""
        role = str(claims.get("role") or "").lower()
        if view.author_id != uid and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        ok = await container.nodes_service.delete(node_id)
        return {"ok": bool(ok)}

    return router
