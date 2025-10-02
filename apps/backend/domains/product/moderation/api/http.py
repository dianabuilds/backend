from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.backend import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def _split_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [v.strip() for v in value.split(",") if v.strip()]
    return parts or None


class CaseCreate(BaseModel):
    title: str
    description: str | None = None
    type: str | None = Field(default="general")
    status: str | None = Field(default="open")
    queue: str | None = None
    priority: str | None = None
    severity: str | None = None
    subject_id: str | None = None
    subject_type: str | None = None
    subject_label: str | None = None
    assignee_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseNoteCreate(BaseModel):
    text: str
    pinned: bool | None = None
    visibility: str | None = None


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    status: str | None = Field(default=None)
    queue: str | None = Field(default=None)
    priority: str | None = Field(default=None)
    severity: str | None = Field(default=None)
    assignee_id: str | None = Field(default=None)
    tags: list[str] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/moderation", tags=["moderation"])

    @router.get("/cases")
    async def list_cases(
        page: int = 1,
        size: int = 20,
        statuses: str | None = None,
        types: str | None = None,
        queues: str | None = None,
        assignee: str | None = None,
        q: str | None = None,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        svc = container.moderation_service
        return await svc.list(
            page=page,
            size=size,
            statuses=_split_csv(statuses),
            types=_split_csv(types),
            queues=_split_csv(queues),
            assignees=_split_csv(assignee),
            query=q,
        )

    @router.get("/cases/{case_id}")
    async def get_case(
        case_id: str,
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        svc = container.moderation_service
        data = await svc.get(case_id)
        if not data:
            raise HTTPException(status_code=404, detail="not_found")
        return data

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
        author_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        return await svc.create(payload, author_id=author_id)

    @router.patch("/cases/{case_id}")
    async def update_case(
        case_id: str,
        body: CaseUpdate,
        _admin: None = Depends(require_admin),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        svc = container.moderation_service
        payload = body.model_dump(exclude_unset=True)
        actor_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        updated = await svc.update(case_id, payload, actor_id=actor_id)
        if not updated:
            raise HTTPException(status_code=404, detail="not_found")
        return updated

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
        author_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        res = await svc.add_note(case_id, note, author_id=author_id)
        if not res:
            raise HTTPException(status_code=404, detail="not_found")
        return res

    return router
