from __future__ import annotations

from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from apps.backend import get_container
from domains.platform.iam.security import require_admin  # type: ignore[import-not-found]
from domains.product.nodes.application.admin_queries import (
    AdminQueryError,
    _analytics_to_csv,
    _ensure_engine,
    _fetch_analytics,
    _parse_query_datetime,
    _resolve_node_id,
)

from ._memory_utils import resolve_memory_node


def _wrap_admin_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AdminQueryError as exc:
            raise HTTPException(
                status_code=exc.status_code, detail=exc.detail
            ) from exc.__cause__

    return wrapper


def register_analytics_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/analytics", summary="Get node engagement analytics")
    @_wrap_admin_errors
    async def get_node_analytics(
        node_id: str,
        start: str | None = Query(default=None),
        end: str | None = Query(default=None),
        limit: int = Query(default=30, ge=1, le=365),
        response_format: str | None = Query(default=None, alias="format"),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        engine = await _ensure_engine(container)
        if engine is not None:
            try:
                resolved_id = await _resolve_node_id(node_id, container, engine)
                start_dt = _parse_query_datetime(start, field="start")
                end_dt = _parse_query_datetime(end, field="end")
                analytics = await _fetch_analytics(
                    engine,
                    node_id=resolved_id,
                    start=start_dt,
                    end=end_dt,
                    limit=limit,
                )
                if response_format and response_format.lower() == "csv":
                    csv_content = _analytics_to_csv(analytics)
                    filename = f"node-{resolved_id}-analytics.csv"
                    return Response(
                        content=csv_content,
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": f'attachment; filename="{filename}"'
                        },
                    )
                return analytics
            except Exception:
                engine = None
        dto = await resolve_memory_node(container, node_id)
        if dto is None:
            raise HTTPException(status_code=404, detail="not_found")
        node_pk = int(dto.id)
        service = container.nodes_service
        total_views = await service.get_total_views(node_pk)
        analytics = {
            "id": str(node_pk),
            "range": {"start": start, "end": end},
            "views": {
                "total": int(total_views or 0),
                "buckets": [],
                "last_updated_at": None,
            },
            "reactions": {"totals": {}, "last_reaction_at": None},
            "comments": {
                "total": 0,
                "by_status": {},
                "last_created_at": None,
            },
        }
        if response_format and response_format.lower() == "csv":
            csv_content = _analytics_to_csv(analytics)
            filename = f"node-{node_pk}-analytics.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        return analytics
