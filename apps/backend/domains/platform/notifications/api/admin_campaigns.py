from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, model_validator

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except ImportError:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin
from domains.platform.notifications.application.broadcast_service import (
    BroadcastCreateInput,
    BroadcastNotFoundError,
    BroadcastService,
    BroadcastStatusError,
    BroadcastUpdateInput,
    BroadcastValidationError,
)
from domains.platform.notifications.domain.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastStatus,
)


class BroadcastAudiencePayload(BaseModel):
    type: BroadcastAudienceType
    filters: dict[str, Any] | None = None
    user_ids: list[str] | None = None

    class Config:
        use_enum_values = True

    @model_validator(mode="before")
    def validate_payload(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(values, dict):
            return values
        raw_type = values.get("type")
        try:
            audience_type = BroadcastAudienceType(raw_type)
        except ValueError as exc:
            raise ValueError(f"unknown audience type: {raw_type!r}") from exc
        values["type"] = audience_type
        filters = values.get("filters")
        user_ids = values.get("user_ids")

        if audience_type is BroadcastAudienceType.ALL_USERS:
            if filters or user_ids:
                raise ValueError(
                    "all_users audience cannot include filters or user_ids"
                )
        elif audience_type is BroadcastAudienceType.SEGMENT:
            if not filters:
                raise ValueError("segment audience requires non-empty filters")
            if user_ids:
                raise ValueError("segment audience cannot include user_ids")
        elif audience_type is BroadcastAudienceType.EXPLICIT_USERS:
            if not user_ids:
                raise ValueError("explicit_users audience requires user_ids")
            if filters:
                raise ValueError("explicit_users audience cannot include filters")
        return values


class BroadcastCreateRequest(BaseModel):
    title: str
    body: str | None = None
    template_id: str | None = None
    audience: BroadcastAudiencePayload
    created_by: str
    scheduled_at: datetime | None = None

    @model_validator(mode="after")
    def ensure_timezone(cls, model: BroadcastCreateRequest) -> BroadcastCreateRequest:
        scheduled_at = model.scheduled_at
        if scheduled_at and scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return model


class BroadcastUpdateRequest(BaseModel):
    title: str
    body: str | None = None
    template_id: str | None = None
    audience: BroadcastAudiencePayload
    scheduled_at: datetime | None = None

    @model_validator(mode="after")
    def ensure_timezone(cls, model: BroadcastUpdateRequest) -> BroadcastUpdateRequest:
        scheduled_at = model.scheduled_at
        if scheduled_at and scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return model


class BroadcastScheduleRequest(BaseModel):
    scheduled_at: datetime

    @model_validator(mode="after")
    def ensure_timezone(
        cls, model: BroadcastScheduleRequest
    ) -> BroadcastScheduleRequest:
        scheduled_at = model.scheduled_at
        if scheduled_at and scheduled_at.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return model


class BroadcastAudienceResponse(BaseModel):
    type: BroadcastAudienceType
    filters: dict[str, Any] | None
    user_ids: list[str] | None

    class Config:
        use_enum_values = True


class BroadcastResponse(BaseModel):
    id: str
    title: str
    body: str | None
    template_id: str | None
    audience: BroadcastAudienceResponse
    status: BroadcastStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    scheduled_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    total: int
    sent: int
    failed: int

    class Config:
        use_enum_values = True


class BroadcastListResponse(BaseModel):
    items: list[BroadcastResponse]
    total: int
    offset: int
    limit: int
    has_next: bool
    status_counts: dict[str, int]
    recipients: int


def make_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1/notifications/admin",
        tags=["admin-notifications"],
    )

    def _get_service(req: Request) -> BroadcastService:
        container = get_container(req)
        return container.notifications.broadcasts

    def _audience_from_payload(payload: BroadcastAudiencePayload) -> BroadcastAudience:
        audience = BroadcastAudience(
            type=BroadcastAudienceType(payload.type),
            filters=payload.filters,
            user_ids=tuple(payload.user_ids) if payload.user_ids else None,
        )
        audience.validate()
        return audience

    def _audience_to_response(audience: BroadcastAudience) -> BroadcastAudienceResponse:
        return BroadcastAudienceResponse(
            type=audience.type,
            filters=audience.filters,
            user_ids=list(audience.user_ids) if audience.user_ids else None,
        )

    def _broadcast_to_response(broadcast: Broadcast) -> BroadcastResponse:
        return BroadcastResponse(
            id=broadcast.id,
            title=broadcast.title,
            body=broadcast.body,
            template_id=broadcast.template_id,
            audience=_audience_to_response(broadcast.audience),
            status=broadcast.status,
            created_by=broadcast.created_by,
            created_at=broadcast.created_at,
            updated_at=broadcast.updated_at,
            scheduled_at=broadcast.scheduled_at,
            started_at=broadcast.started_at,
            finished_at=broadcast.finished_at,
            total=broadcast.total,
            sent=broadcast.sent,
            failed=broadcast.failed,
        )

    @router.get(
        "/broadcasts",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
        response_model=BroadcastListResponse,
    )
    async def list_broadcasts(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        status: list[BroadcastStatus] | None = Query(default=None),
        q: str | None = Query(default=None, min_length=1, max_length=120),
        _admin: None = Depends(require_admin),
    ) -> BroadcastListResponse:
        service = _get_service(req)
        result = await service.list(
            limit=limit, offset=offset, statuses=status, query=q
        )
        items = [_broadcast_to_response(item) for item in result.items]
        counts = {
            status.value: result.status_counts.get(status, 0)
            for status in BroadcastStatus
        }
        has_next = offset + len(items) < result.total
        return BroadcastListResponse(
            items=items,
            total=result.total,
            offset=offset,
            limit=limit,
            has_next=has_next,
            status_counts=counts,
            recipients=result.recipient_total,
        )

    @router.post(
        "/broadcasts",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
        response_model=BroadcastResponse,
    )
    async def create_broadcast(
        req: Request,
        payload: BroadcastCreateRequest,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        service = _get_service(req)
        try:
            audience = _audience_from_payload(payload.audience)
            data = BroadcastCreateInput(
                title=payload.title,
                body=payload.body,
                template_id=payload.template_id,
                audience=audience,
                created_by=payload.created_by,
                scheduled_at=payload.scheduled_at,
            )
            broadcast = await service.create(data)
        except BroadcastValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _broadcast_to_response(broadcast)

    @router.put(
        "/broadcasts/{broadcast_id}",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
        response_model=BroadcastResponse,
    )
    async def update_broadcast(
        req: Request,
        broadcast_id: str,
        payload: BroadcastUpdateRequest,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        service = _get_service(req)
        try:
            audience = _audience_from_payload(payload.audience)
            data = BroadcastUpdateInput(
                title=payload.title,
                body=payload.body,
                template_id=payload.template_id,
                audience=audience,
                scheduled_at=payload.scheduled_at,
            )
            broadcast = await service.update(broadcast_id, data)
        except BroadcastNotFoundError:
            raise HTTPException(status_code=404, detail="broadcast not found") from None
        except BroadcastStatusError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BroadcastValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _broadcast_to_response(broadcast)

    @router.post(
        "/broadcasts/{broadcast_id}/actions/send-now",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
        response_model=BroadcastResponse,
    )
    async def send_now(
        req: Request,
        broadcast_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        service = _get_service(req)
        try:
            broadcast = await service.send_now(broadcast_id)
        except BroadcastNotFoundError:
            raise HTTPException(status_code=404, detail="broadcast not found") from None
        except BroadcastStatusError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _broadcast_to_response(broadcast)

    @router.post(
        "/broadcasts/{broadcast_id}/actions/schedule",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
        response_model=BroadcastResponse,
    )
    async def schedule(
        req: Request,
        broadcast_id: str,
        payload: BroadcastScheduleRequest,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        service = _get_service(req)
        try:
            broadcast = await service.schedule(broadcast_id, payload.scheduled_at)
        except BroadcastNotFoundError:
            raise HTTPException(status_code=404, detail="broadcast not found") from None
        except BroadcastStatusError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except BroadcastValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _broadcast_to_response(broadcast)

    @router.post(
        "/broadcasts/{broadcast_id}/actions/cancel",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
        response_model=BroadcastResponse,
    )
    async def cancel(
        req: Request,
        broadcast_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        service = _get_service(req)
        try:
            broadcast = await service.cancel(broadcast_id)
        except BroadcastNotFoundError:
            raise HTTPException(status_code=404, detail="broadcast not found") from None
        except BroadcastStatusError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _broadcast_to_response(broadcast)

    return router
