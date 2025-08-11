from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from sqlalchemy import func

from app.api.deps import require_role
from app.db.session import get_db
from app.models.echo_trace import EchoTrace
from app.models.node import Node
from app.models.user import User
from app.schemas.echo import AdminEchoTraceOut, PopularityRecomputeRequest
from app.services.navcache import navcache
from app.core.log_events import cache_invalidate
from app.core.audit_log import log_admin_action

router = APIRouter(prefix="/admin/echo", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[AdminEchoTraceOut], summary="List echo traces")
async def list_echo_traces(
    from_slug: str | None = Query(None, alias="from"),
    to_slug: str | None = Query(None, alias="to"),
    user_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    from_node = aliased(Node)
    to_node = aliased(Node)
    stmt = (
        select(EchoTrace, from_node.slug, to_node.slug)
        .join(from_node, EchoTrace.from_node_id == from_node.id)
        .join(to_node, EchoTrace.to_node_id == to_node.id)
    )
    if from_slug:
        stmt = stmt.where(from_node.slug == from_slug)
    if to_slug:
        stmt = stmt.where(to_node.slug == to_slug)
    if user_id:
        stmt = stmt.where(EchoTrace.user_id == user_id)
    if date_from:
        stmt = stmt.where(EchoTrace.created_at >= date_from)
    if date_to:
        stmt = stmt.where(EchoTrace.created_at <= date_to)
    stmt = stmt.order_by(EchoTrace.created_at.desc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        AdminEchoTraceOut(
            id=t.id,
            from_slug=fs,
            to_slug=ts,
            user_id=t.user_id,
            source=t.source,
            channel=t.channel,
            created_at=t.created_at,
        )
        for t, fs, ts in rows
    ]


@router.post("/{trace_id}/anonymize", summary="Anonymize echo trace")
async def anonymize_echo_trace(
    trace_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    trace = await db.get(EchoTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Echo trace not found")
    trace.user_id = None
    await db.commit()
    await log_admin_action(db, actor_id=current_user.id, action="anonymize_echo", resource_type="echo", resource_id=str(trace_id))
    return {"status": "ok"}


@router.delete("/{trace_id}", summary="Delete echo trace")
async def delete_echo_trace(
    trace_id: UUID,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    trace = await db.get(EchoTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Echo trace not found")
    await db.delete(trace)
    await db.commit()
    await log_admin_action(db, actor_id=current_user.id, action="delete_echo", resource_type="echo", resource_id=str(trace_id))
    return {"status": "deleted"}


@router.post("/recompute_popularity", summary="Recompute node popularity")
async def recompute_popularity(
    payload: PopularityRecomputeRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Node)
    if payload.node_slugs:
        stmt = stmt.where(Node.slug.in_(payload.node_slugs))
    nodes = (await db.execute(stmt)).scalars().all()
    if not nodes:
        return {"updated": 0}
    node_ids = [n.id for n in nodes]
    count_stmt = select(EchoTrace.to_node_id, func.count()).group_by(EchoTrace.to_node_id)
    if node_ids:
        count_stmt = count_stmt.where(EchoTrace.to_node_id.in_(node_ids))
    counts = {nid: cnt for nid, cnt in (await db.execute(count_stmt)).all()}
    for n in nodes:
        n.popularity_score = float(counts.get(n.id, 0))
        await navcache.invalidate_navigation_by_node(n.slug)
        await navcache.invalidate_compass_by_node(n.slug)
        cache_invalidate("nav", reason="recompute_popularity", key=n.slug)
        cache_invalidate("comp", reason="recompute_popularity", key=n.slug)
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="recompute_popularity",
        resource_type="node",
        resource_id=",".join(payload.node_slugs) if payload.node_slugs else "all",
    )
    return {"updated": len(nodes)}
