from __future__ import annotations

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException, Request

from domains.platform.iam.security import csrf_protect, get_current_user
from domains.product.quests.application.ports import CreateQuestInput


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/quests")

    @router.get("/{quest_id}")
    def get_quest(
        quest_id: str,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        svc = container.quests_service
        view = svc.get(quest_id)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin" and not view.is_public:
            raise HTTPException(status_code=404, detail="not_found")
        return {
            "id": view.id,
            "author_id": view.author_id,
            "slug": view.slug,
            "title": view.title,
            "description": view.description,
            "tags": list(view.tags),
            "is_public": view.is_public,
        }

    @router.post("")
    def create_quest(
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        uid = str(claims.get("sub")) if claims else None
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        data = CreateQuestInput(
            author_id=uid,
            title=str(body.get("title") or "").strip(),
            description=body.get("description"),
            tags=list(body.get("tags") or []),
            is_public=bool(body.get("is_public", False)),
        )
        if not data.title:
            raise HTTPException(status_code=400, detail="title_required")
        svc = container.quests_service
        view = svc.create(data)
        return {"id": view.id, "slug": view.slug}

    @router.put("/{quest_id}/tags")
    def set_tags(
        quest_id: str,
        body: dict,
        req: Request,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ):
        svc = container.quests_service
        view = svc.get(quest_id)
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        uid = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if view.author_id != (uid or "") and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        tags = body.get("tags") or []
        if not isinstance(tags, list):
            raise HTTPException(status_code=400, detail="tags_list_required")
        updated = svc.update_tags(quest_id, tags, actor_id=uid or "")
        return {"id": updated.id, "tags": list(updated.tags)}

    return router
