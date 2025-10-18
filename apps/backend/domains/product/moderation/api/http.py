from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_admin,
)
from domains.product.moderation.application.interactors.cases import (
    ModerationCaseCreateCommand,
    ModerationCaseFilters,
    ModerationCaseNoteCommand,
    ModerationCaseUpdateCommand,
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
        status_values = _split_csv(statuses)
        type_values = _split_csv(types)
        queue_values = _split_csv(queues)
        assignee_values = _split_csv(assignee)
        filters = ModerationCaseFilters(
            page=int(page),
            size=int(size),
            statuses=tuple(status_values) if status_values else None,
            types=tuple(type_values) if type_values else None,
            queues=tuple(queue_values) if queue_values else None,
            assignees=tuple(assignee_values) if assignee_values else None,
            query=q,
        )
        return await svc.list(filters)

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
        author_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        command = ModerationCaseCreateCommand(
            title=body.title,
            description=body.description,
            type=body.type or "general",
            status=body.status or "open",
            queue=body.queue,
            priority=body.priority,
            severity=body.severity,
            subject_id=body.subject_id,
            subject_type=body.subject_type,
            subject_label=body.subject_label,
            assignee_id=body.assignee_id,
            tags=tuple(body.tags) if body.tags else tuple(),
            metadata=body.metadata or {},
            author_id=author_id,
        )
        return await svc.create(command)

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
        command = ModerationCaseUpdateCommand(
            case_id=case_id,
            actor_id=actor_id,
            title=payload.get("title"),
            description=payload.get("description"),
            status=payload.get("status"),
            queue=payload.get("queue"),
            priority=payload.get("priority"),
            severity=payload.get("severity"),
            assignee_id=payload.get("assignee_id"),
            tags=(
                tuple(payload["tags"])
                if "tags" in payload and payload["tags"] is not None
                else None
            ),
            metadata=payload.get("metadata"),
        )
        updated = await svc.update(command)
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
        author_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        command = ModerationCaseNoteCommand(
            case_id=case_id,
            text=body.text,
            author_id=author_id,
            pinned=body.pinned,
            visibility=body.visibility,
        )
        res = await svc.add_note(command)
        if not res:
            raise HTTPException(status_code=404, detail="not_found")
        return res

    return router
