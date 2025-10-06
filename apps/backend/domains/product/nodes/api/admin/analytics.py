from __future__ import annotations

from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from apps.backend import get_container
from domains.platform.iam.security import require_admin  # type: ignore[import-not-found]
from domains.product.nodes.adapters.memory.utils import resolve_memory_node
from domains.product.nodes.application.admin_queries import (
    AdminQueryError,
    build_analytics_csv,
    fetch_node_analytics,
)


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
        result = await fetch_node_analytics(
            container,
            node_identifier=node_id,
            start=start,
            end=end,
            limit=limit,
        )
        if result is not None:
            analytics = result["payload"]
            if response_format and response_format.lower() == "csv":
                csv_content = build_analytics_csv(analytics)
                filename = f"node-{result['node_id']}-analytics.csv"
                return Response(
                    content=csv_content,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f'attachment; filename="{filename}"'
                    },
                )
            return analytics

        dto = await resolve_memory_node(container, node_id)
        if dto is None:
            raise HTTPException(status_code=404, detail="not_found")
        node_pk = int(dto.id)
        service = container.nodes_service
        total_views = await service.get_total_views(node_pk)
        normalized_start = start
        normalized_end = end
        analytics = {
            "id": str(node_pk),
            "range": {"start": normalized_start, "end": normalized_end},
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
            csv_content = build_analytics_csv(analytics)
            filename = f"node-{node_pk}-analytics.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        return analytics
