from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.backendDDD.app.api_gateway.routers import get_container
from apps.backendDDD.domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/moderation", tags=["moderation"])

    @router.get("/cases")
    async def list_cases(
        page: int = 1,
        size: int = 20,
        statuses: str | None = None,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        svc = container.moderation_service
        sts = [s.strip() for s in (statuses or "").split(",") if s.strip()] or None
        return await svc.list(page=page, size=size, statuses=sts)

    @router.post("/cases")
    class CaseCreate(BaseModel):
        title: str
        description: str | None = None

    @router.post("/cases")
    async def create_case(
        body: CaseCreate,
        _admin: None = Depends(require_admin),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        svc = container.moderation_service
        payload = body.model_dump()
        return await svc.create(payload)

    @router.post("/cases/{case_id}/notes")
    class CaseNoteCreate(BaseModel):
        text: str

    @router.post("/cases/{case_id}/notes")
    async def add_note(
        case_id: str,
        body: CaseNoteCreate,
        _admin: None = Depends(require_admin),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        svc = container.moderation_service
        note = body.model_dump()
        res = await svc.add_note(
            case_id, note, author_id=str(claims.get("sub")) if claims else None
        )
        if not res:
            raise HTTPException(status_code=404, detail="not_found")
        return res

    return router
