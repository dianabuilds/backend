from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from domains.platform.notifications.application.broadcast_exceptions import (
    BroadcastError,
)
from domains.platform.notifications.application.broadcast_presenter import (
    BroadcastListResponse,
    BroadcastPayload,
    broadcast_to_dict,
    build_broadcast_list_response,
)
from domains.platform.notifications.application.broadcast_service import (
    BroadcastCreateInput,
    BroadcastNotFoundError,
    BroadcastService,
    BroadcastStatusError,
    BroadcastUpdateInput,
    BroadcastValidationError,
)
from domains.platform.notifications.domain.broadcast import (
    BroadcastAudience,
    BroadcastAudienceType,
    BroadcastStatus,
)


def _to_broadcast_error(error: Exception) -> BroadcastError:
    if isinstance(error, BroadcastNotFoundError):
        return BroadcastError(
            code="broadcast_not_found",
            status_code=404,
            message="broadcast not found",
        )
    if isinstance(error, BroadcastStatusError):
        return BroadcastError(
            code="invalid_status",
            status_code=409,
            message=str(error),
        )
    if isinstance(error, BroadcastValidationError):
        return BroadcastError(
            code="invalid_broadcast",
            status_code=400,
            message=str(error) or "invalid broadcast",
        )
    raise error


def _coerce_audience_type(value: Any) -> BroadcastAudienceType:
    if isinstance(value, BroadcastAudienceType):
        return value
    if isinstance(value, str):
        try:
            return BroadcastAudienceType(value)
        except ValueError as exc:
            raise BroadcastError(
                code="invalid_audience",
                status_code=400,
                message=f"unknown audience type: {value!r}",
            ) from exc
    raise BroadcastError(
        code="invalid_audience",
        status_code=400,
        message="audience type is required",
    )


def _normalize_filters(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise BroadcastError(
            code="invalid_audience",
            status_code=400,
            message="audience filters must be an object",
        )
    return dict(value)


def _normalize_user_ids(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise BroadcastError(
            code="invalid_audience",
            status_code=400,
            message="audience user_ids must be an array",
        )
    normalized = [str(item).strip() for item in value if str(item).strip()]
    if not normalized:
        return None
    return tuple(normalized)


def _build_audience(payload: Any) -> BroadcastAudience:
    if not isinstance(payload, Mapping):
        raise BroadcastError(
            code="invalid_audience",
            status_code=400,
            message="audience payload must be an object",
        )
    audience_type = _coerce_audience_type(payload.get("type"))
    filters = _normalize_filters(payload.get("filters"))
    user_ids = _normalize_user_ids(payload.get("user_ids"))
    audience = BroadcastAudience(
        type=audience_type,
        filters=filters,
        user_ids=user_ids,
    )
    try:
        audience.validate()
    except ValueError as exc:
        raise BroadcastError(
            code="invalid_audience",
            status_code=400,
            message=str(exc),
        ) from exc
    return audience


def _normalize_statuses(
    statuses: Sequence[BroadcastStatus | str] | None,
) -> tuple[BroadcastStatus, ...] | None:
    if not statuses:
        return None
    normalized: list[BroadcastStatus] = []
    for item in statuses:
        if isinstance(item, BroadcastStatus):
            normalized.append(item)
            continue
        if isinstance(item, str):
            try:
                normalized.append(BroadcastStatus(item))
                continue
            except ValueError as exc:
                raise BroadcastError(
                    code="invalid_status_filter",
                    status_code=400,
                    message=f"unknown status: {item}",
                ) from exc
        raise BroadcastError(
            code="invalid_status_filter",
            status_code=400,
            message="status filter must be a string",
        )
    return tuple(normalized)


def _require_mapping(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise BroadcastError(
            code="invalid_broadcast",
            status_code=400,
            message="payload must be an object",
        )
    return payload


def _require_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise BroadcastError(
            code="invalid_broadcast",
            status_code=400,
            message=f"{key} must be a string",
        )
    return value


def _optional_str(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise BroadcastError(
            code="invalid_broadcast",
            status_code=400,
            message=f"{key} must be a string",
        )
    return value


def _optional_datetime(payload: Mapping[str, Any], key: str) -> datetime | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise BroadcastError(
            code="invalid_broadcast",
            status_code=400,
            message=f"{key} must be a datetime",
        )
    return value


async def list_broadcasts(
    service: BroadcastService,
    *,
    limit: int,
    offset: int,
    statuses: Sequence[BroadcastStatus | str] | None = None,
    query: str | None = None,
) -> BroadcastListResponse:
    normalized_statuses = _normalize_statuses(statuses)
    collection = await service.list(
        limit=limit,
        offset=offset,
        statuses=normalized_statuses,
        query=query,
    )
    payload = build_broadcast_list_response(collection, limit=limit, offset=offset)
    return payload


async def create_broadcast(
    service: BroadcastService,
    payload: Any,
) -> BroadcastPayload:
    data = _require_mapping(payload)
    audience = _build_audience(data.get("audience"))
    title = _require_str(data, "title")
    created_by = _require_str(data, "created_by")
    body = _optional_str(data, "body")
    template_id = _optional_str(data, "template_id")
    scheduled_at = _optional_datetime(data, "scheduled_at")
    input_data = BroadcastCreateInput(
        title=title,
        body=body,
        template_id=template_id,
        audience=audience,
        created_by=created_by,
        scheduled_at=scheduled_at,
    )
    try:
        broadcast = await service.create(input_data)
    except BroadcastValidationError as exc:
        raise _to_broadcast_error(exc) from exc
    return broadcast_to_dict(broadcast)


async def update_broadcast(
    service: BroadcastService,
    broadcast_id: str,
    payload: Any,
) -> BroadcastPayload:
    data = _require_mapping(payload)
    audience = _build_audience(data.get("audience"))
    title = _require_str(data, "title")
    body = _optional_str(data, "body")
    template_id = _optional_str(data, "template_id")
    scheduled_at = _optional_datetime(data, "scheduled_at")
    input_data = BroadcastUpdateInput(
        title=title,
        body=body,
        template_id=template_id,
        audience=audience,
        scheduled_at=scheduled_at,
    )
    try:
        broadcast = await service.update(broadcast_id, input_data)
    except (
        BroadcastNotFoundError,
        BroadcastStatusError,
        BroadcastValidationError,
    ) as exc:
        raise _to_broadcast_error(exc) from exc
    return broadcast_to_dict(broadcast)


async def send_broadcast_now(
    service: BroadcastService,
    broadcast_id: str,
) -> BroadcastPayload:
    try:
        broadcast = await service.send_now(broadcast_id)
    except (BroadcastNotFoundError, BroadcastStatusError) as exc:
        raise _to_broadcast_error(exc) from exc
    return broadcast_to_dict(broadcast)


async def schedule_broadcast(
    service: BroadcastService,
    broadcast_id: str,
    scheduled_at: datetime,
) -> BroadcastPayload:
    if not isinstance(scheduled_at, datetime):
        raise BroadcastError(
            code="invalid_broadcast",
            status_code=400,
            message="scheduled_at must be a datetime",
        )
    try:
        broadcast = await service.schedule(broadcast_id, scheduled_at)
    except (
        BroadcastNotFoundError,
        BroadcastStatusError,
        BroadcastValidationError,
    ) as exc:
        raise _to_broadcast_error(exc) from exc
    return broadcast_to_dict(broadcast)


async def cancel_broadcast(
    service: BroadcastService,
    broadcast_id: str,
) -> BroadcastPayload:
    try:
        broadcast = await service.cancel(broadcast_id)
    except (BroadcastNotFoundError, BroadcastStatusError) as exc:
        raise _to_broadcast_error(exc) from exc
    return broadcast_to_dict(broadcast)


__all__ = [
    "cancel_broadcast",
    "create_broadcast",
    "list_broadcasts",
    "schedule_broadcast",
    "send_broadcast_now",
    "update_broadcast",
]
