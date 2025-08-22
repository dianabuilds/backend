from __future__ import annotations

from typing import Any, Dict, List, Mapping

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import admin_required
from app.core.db.session import get_db
from app.domains.ai.infrastructure.models.generation_models import GenerationJob
from app.core.pagination import (
    parse_page_query,
    extract_filters,
    apply_filters,
    apply_sorting,
    apply_pagination,
    decode_cursor,
    build_cursor_for_last_item,
    fetch_page,
    FilterSpec,
)

router = APIRouter(prefix="/admin/ai/quests", tags=["admin-ai-quests"])


@router.get("/jobs_cursor")
async def list_jobs_cursor(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_required),
):
    params: Mapping[str, str] = dict(request.query_params)
    pq = parse_page_query(params, allowed_sort=["created_at"], default_sort="created_at")

    def _status(v: str) -> str:
        allowed = {"queued", "running", "completed", "failed", "canceled"}
        if v not in allowed:
            raise ValueError("invalid status")
        return v

    spec: FilterSpec = {
        "status": (_status, lambda stmt, v: stmt.where(GenerationJob.status == v)),
    }
    filters = extract_filters(params)

    stmt = select(GenerationJob)
    stmt, applied_filters = apply_filters(stmt, filters, spec)
    stmt = apply_sorting(stmt, model=GenerationJob, sort_field=pq.sort, order=pq.order)

    cursor = decode_cursor(pq.cursor) if pq.cursor else None
    stmt = apply_pagination(stmt, model=GenerationJob, cursor=cursor, sort_field=pq.sort, order=pq.order)

    items, has_next = await fetch_page(stmt, session=db, limit=pq.limit)
    next_cursor = build_cursor_for_last_item(items[-1], pq.sort, pq.order) if has_next and items else None

    out: List[Dict[str, Any]] = []
    for j in items:
        out.append(
            {
                "id": str(j.id),
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "created_by": str(j.created_by) if j.created_by else None,
                "provider": j.provider,
                "model": j.model,
                "params": j.params,
                "result_quest_id": str(j.result_quest_id) if j.result_quest_id else None,
                "result_version_id": str(j.result_version_id) if j.result_version_id else None,
                "cost": float(j.cost) if j.cost is not None else None,
                "token_usage": j.token_usage,
                "reused": bool(j.reused),
                "progress": int(j.progress or 0),
                "logs": j.logs or None,
                "error": j.error,
            }
        )

    return {
        "limit": pq.limit,
        "sort": pq.sort,
        "order": pq.order,
        "filters": applied_filters,
        "items": out,
        "next_cursor": next_cursor,
    }
