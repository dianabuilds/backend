from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased
from sqlalchemy import func, literal, text

from app.db.session import get_db
from app.domains.navigation.infrastructure.models.echo_models import EchoTrace
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.schemas.echo import AdminEchoTraceOut, PopularityRecomputeRequest
from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.core.log_events import cache_invalidate
from app.core.audit_log import log_admin_action
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from pydantic import BaseModel

admin_required = require_admin_role()
admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/echo",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)
logger = logging.getLogger(__name__)

navcache = NavigationCacheService(CoreCacheAdapter())


class BulkIds(BaseModel):
    ids: List[UUID]


@router.get("", response_model=list[AdminEchoTraceOut], summary="List echo traces")
async def list_echo_traces(
    from_slug: str | None = Query(None, alias="from"),
    to_slug: str | None = Query(None, alias="to"),
    user_id: UUID | None = None,
    source: str | None = None,
    channel: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    from_node = aliased(Node)
    to_node = aliased(Node)

    has_source = False
    has_channel = False
    try:
        res = await db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = :t "
                "AND column_name IN ('source','channel')"
            ),
            {"t": EchoTrace.__tablename__},
        )
        present = set(res.scalars().all())
        has_source = "source" in present
        has_channel = "channel" in present
    except Exception:
        has_source = False
        has_channel = False

    cols = [
        EchoTrace.id.label("id"),
        EchoTrace.user_id.label("user_id"),
        EchoTrace.created_at.label("created_at"),
        from_node.slug.label("from_slug"),
        to_node.slug.label("to_slug"),
        (EchoTrace.source if has_source else literal(None)).label("source"),
        (EchoTrace.channel if has_channel else literal(None)).label("channel"),
    ]

    stmt = (
        select(*cols)
        .join(from_node, EchoTrace.from_node_id == from_node.id)
        .join(to_node, EchoTrace.to_node_id == to_node.id)
    )

    if from_slug:
        stmt = stmt.where(from_node.slug == from_slug)
    if to_slug:
        stmt = stmt.where(to_node.slug == to_slug)
    if user_id:
        stmt = stmt.where(EchoTrace.user_id == user_id)
    if source and has_source:
        stmt = stmt.where(EchoTrace.source == source)
    if channel and has_channel:
        stmt = stmt.where(EchoTrace.channel == channel)
    if date_from:
        stmt = stmt.where(EchoTrace.created_at >= date_from)
    if date_to:
        stmt = stmt.where(EchoTrace.created_at <= date_to)

    stmt = stmt.order_by(EchoTrace.created_at.desc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    rows = result.all()

    data: list[AdminEchoTraceOut] = []
    for r in rows:
        m = r._mapping
        data.append(
            AdminEchoTraceOut(
                id=m["id"],
                from_slug=m["from_slug"],
                to_slug=m["to_slug"],
                user_id=m.get("user_id"),
                source=m.get("source"),
                channel=m.get("channel"),
                created_at=m["created_at"],
            )
        )
    return data


@router.post("/{trace_id}/anonymize", summary="Anonymize echo trace")
async def anonymize_echo_trace(
    trace_id: UUID,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    trace = await db.get(EchoTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Echo trace not found")
    trace.user_id = None
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="anonymize_echo",
        resource_type="echo",
        resource_id=str(trace_id),
    )
    return {"status": "ok"}


@router.delete("/{trace_id}", summary="Delete echo trace")
async def delete_echo_trace(
    trace_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    trace = await db.get(EchoTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Echo trace not found")
    await db.delete(trace)
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="delete_echo",
        resource_type="echo",
        resource_id=str(trace_id),
    )
    return {"status": "deleted"}


@router.post("/bulk/anonymize", summary="Bulk anonymize echo traces")
async def bulk_anonymize_echo(
    payload: BulkIds,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    if not payload.ids:
        return {"updated": 0}
    result = await db.execute(select(EchoTrace).where(EchoTrace.id.in_(payload.ids)))
    traces = result.scalars().all()
    for t in traces:
        t.user_id = None
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="bulk_anonymize_echo",
        resource_type="echo",
        resource_id=",".join(str(i) for i in payload.ids),
    )
    return {"updated": len(traces)}


@router.post("/bulk/delete", summary="Bulk delete echo traces")
async def bulk_delete_echo(
    payload: BulkIds,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    if not payload.ids:
        return {"deleted": 0}
    result = await db.execute(select(EchoTrace).where(EchoTrace.id.in_(payload.ids)))
    traces = result.scalars().all()
    for t in traces:
        await db.delete(t)
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="bulk_delete_echo",
        resource_type="echo",
        resource_id=",".join(str(i) for i in payload.ids),
    )
    return {"deleted": len(traces)}


@router.post("/recompute_popularity", summary="Recompute node popularity")
async def recompute_popularity(
    payload: PopularityRecomputeRequest,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Node)
    if payload.node_slugs:
        stmt = stmt.where(Node.slug.in_(payload.node_slugs))
    nodes = (await db.execute(stmt)).scalars().all()
    if not nodes:
        return {"updated": 0}
    node_ids = [n.id for n in nodes]
    count_stmt = select(EchoTrace.to_node_id, func.count()).group_by(
        EchoTrace.to_node_id
    )
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
