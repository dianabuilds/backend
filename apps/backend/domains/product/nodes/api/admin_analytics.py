from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from apps.backend import get_container
from domains.platform.iam.security import require_admin  # type: ignore[import-not-found]

from .admin_common import (
    _analytics_to_csv,
    _ensure_engine,
    _fetch_analytics,
    _parse_query_datetime,
    _resolve_node_id,
)


def register_analytics_routes(router: APIRouter) -> None:
    @router.get("/{node_id}/analytics", summary="Get node engagement analytics")
    async def get_node_analytics(
        node_id: str,
        start: str | None = Query(default=None),
        end: str | None = Query(default=None),
        limit: int = Query(default=30, ge=1, le=365),
        response_format: str | None = Query(default=None),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        engine = await _ensure_engine(container)
        if engine is None:
            raise HTTPException(status_code=503, detail="database_unavailable")
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
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        return analytics
