from __future__ import annotations

from datetime import datetime
from typing import Any

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, field_validator, model_validator

from domains.platform.iam.security import csrf_protect, require_admin
from domains.platform.notifications.application.broadcast_exceptions import (
    BroadcastError,
)
from domains.platform.notifications.application.broadcast_service import (
    BroadcastService,
)
from domains.platform.notifications.application.broadcast_use_cases import (
    cancel_broadcast as cancel_broadcast_use_case,
)
from domains.platform.notifications.application.broadcast_use_cases import (
    create_broadcast as create_broadcast_use_case,
)
from domains.platform.notifications.application.broadcast_use_cases import (
    list_broadcasts as list_broadcasts_use_case,
)
from domains.platform.notifications.application.broadcast_use_cases import (
    schedule_broadcast as schedule_broadcast_use_case,
)
from domains.platform.notifications.application.broadcast_use_cases import (
    send_broadcast_now as send_broadcast_now_use_case,
)
from domains.platform.notifications.application.broadcast_use_cases import (
    update_broadcast as update_broadcast_use_case,
)
from domains.platform.notifications.domain.broadcast import (
    BroadcastAudienceType,
    BroadcastStatus,
)
from packages.fastapi_rate_limit import optional_rate_limiter


class BroadcastAudiencePayload(BaseModel):
    type: BroadcastAudienceType
    filters: dict[str, Any] | None = None
    user_ids: list[str] | None = None

    class Config:
        use_enum_values = True

    @classmethod
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

    @classmethod
    @field_validator("scheduled_at")
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value and value.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return value


class BroadcastUpdateRequest(BaseModel):
    title: str
    body: str | None = None
    template_id: str | None = None
    audience: BroadcastAudiencePayload
    scheduled_at: datetime | None = None

    @classmethod
    @field_validator("scheduled_at")
    def ensure_timezone(cls, value: datetime | None) -> datetime | None:
        if value and value.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return value


class BroadcastScheduleRequest(BaseModel):
    scheduled_at: datetime

    @classmethod
    @field_validator("scheduled_at")
    def ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return value


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

    def _raise_broadcast_error(error: BroadcastError) -> None:
        headers = error.headers or None
        raise HTTPException(
            status_code=error.status_code,
            detail=error.message,
            headers=headers,
        ) from error

    @router.get(
        "/broadcasts",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
        response_model=BroadcastListResponse,
    )
    async def list_broadcasts(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        statuses: list[BroadcastStatus] | None = Query(default=None),
        q: str | None = Query(default=None, min_length=1, max_length=120),
        _admin: None = Depends(require_admin),
    ) -> BroadcastListResponse:
        try:
            result = await list_broadcasts_use_case(
                _get_service(req),
                limit=limit,
                offset=offset,
                statuses=statuses,
                query=q,
            )
        except BroadcastError as error:
            _raise_broadcast_error(error)
        return BroadcastListResponse(**result)

    @router.post(
        "/broadcasts",
        dependencies=(optional_rate_limiter(times=10, seconds=60)),
        response_model=BroadcastResponse,
    )
    async def create_broadcast(
        req: Request,
        payload: BroadcastCreateRequest,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        try:
            result = await create_broadcast_use_case(
                _get_service(req),
                payload.model_dump(exclude_none=True),
            )
        except BroadcastError as error:
            _raise_broadcast_error(error)
        return BroadcastResponse(**result)

    @router.put(
        "/broadcasts/{broadcast_id}",
        dependencies=(optional_rate_limiter(times=10, seconds=60)),
        response_model=BroadcastResponse,
    )
    async def update_broadcast(
        req: Request,
        broadcast_id: str,
        payload: BroadcastUpdateRequest,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        try:
            result = await update_broadcast_use_case(
                _get_service(req),
                broadcast_id,
                payload.model_dump(exclude_none=True),
            )
        except BroadcastError as error:
            _raise_broadcast_error(error)
        return BroadcastResponse(**result)

    @router.post(
        "/broadcasts/{broadcast_id}/actions/send-now",
        dependencies=(optional_rate_limiter(times=10, seconds=60)),
        response_model=BroadcastResponse,
    )
    async def send_now(
        req: Request,
        broadcast_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        try:
            result = await send_broadcast_now_use_case(
                _get_service(req),
                broadcast_id,
            )
        except BroadcastError as error:
            _raise_broadcast_error(error)
        return BroadcastResponse(**result)

    @router.post(
        "/broadcasts/{broadcast_id}/actions/schedule",
        dependencies=(optional_rate_limiter(times=10, seconds=60)),
        response_model=BroadcastResponse,
    )
    async def schedule(
        req: Request,
        broadcast_id: str,
        payload: BroadcastScheduleRequest,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        try:
            result = await schedule_broadcast_use_case(
                _get_service(req),
                broadcast_id,
                payload.scheduled_at,
            )
        except BroadcastError as error:
            _raise_broadcast_error(error)
        return BroadcastResponse(**result)

    @router.post(
        "/broadcasts/{broadcast_id}/actions/cancel",
        dependencies=(optional_rate_limiter(times=10, seconds=60)),
        response_model=BroadcastResponse,
    )
    async def cancel(
        req: Request,
        broadcast_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> BroadcastResponse:
        try:
            result = await cancel_broadcast_use_case(
                _get_service(req),
                broadcast_id,
            )
        except BroadcastError as error:
            _raise_broadcast_error(error)
        return BroadcastResponse(**result)

    return router


__all__ = ["make_router"]
