from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import literal, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from app.core.audit_log import log_admin_action
from app.core.db.session import get_db
from app.domains.navigation.infrastructure.models.transition_models import NodeTrace
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

logger = logging.getLogger(__name__)

admin_required = require_admin_role()
admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/traces",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


class BulkIds(BaseModel):
    ids: list[UUID]


@router.get("", summary="List navigation traces")
async def list_traces(
    from_slug: Annotated[str | None, Query(alias="from")] = None,
    to_slug: Annotated[str | None, Query(alias="to")] = None,
    user_id: UUID | None = None,
    type: str | None = None,
    source: str | None = None,
    channel: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    from_node = aliased(Node)
    to_node = aliased(Node)

    has_to = has_type = has_source = has_channel = False
    has_latency = has_request = False
    present: set[str] = set()
    try:
        res = await db.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = :t "
                "AND column_name IN ('to_node_id','type','source','channel','latency_ms','request_id')"
            ),
            {"t": NodeTrace.__tablename__},
        )
        present = set(res.scalars().all())
    except Exception:
        try:
            res = await db.execute(
                text(f"PRAGMA table_info({NodeTrace.__tablename__})")
            )
            present = {row[1] for row in res.all()}
        except Exception:
            present = set()

    has_to = "to_node_id" in present
    has_type = "type" in present and hasattr(NodeTrace, "type")
    has_source = "source" in present and hasattr(NodeTrace, "source")
    has_channel = "channel" in present and hasattr(NodeTrace, "channel")
    has_latency = "latency_ms" in present and hasattr(NodeTrace, "latency_ms")
    has_request = "request_id" in present and hasattr(NodeTrace, "request_id")

    cols = [
        NodeTrace.id.label("id"),
        (NodeTrace.user_id if hasattr(NodeTrace, "user_id") else literal(None)).label(
            "user_id"
        ),
        (
            NodeTrace.created_at if hasattr(NodeTrace, "created_at") else literal(None)
        ).label("created_at"),
        from_node.slug.label("from_slug"),
        (to_node.slug if has_to else literal(None)).label("to_slug"),
        (NodeTrace.type if has_type else literal(None)).label("type"),
        (NodeTrace.source if has_source else literal(None)).label("source"),
        (NodeTrace.channel if has_channel else literal(None)).label("channel"),
        (NodeTrace.latency_ms if has_latency else literal(None)).label("latency_ms"),
        (NodeTrace.request_id if has_request else literal(None)).label("request_id"),
    ]

    stmt = select(*cols).join(from_node, NodeTrace.node_id == from_node.id)
    if has_to:
        stmt = stmt.outerjoin(to_node, text("node_traces.to_node_id") == to_node.id)

    if from_slug:
        stmt = stmt.where(from_node.slug == from_slug)
    if to_slug:
        if not has_to:
            raise HTTPException(
                status_code=400, detail="Filtering by to_slug is not supported"
            )
        stmt = stmt.where(to_node.slug == to_slug)
    if user_id and hasattr(NodeTrace, "user_id"):
        stmt = stmt.where(NodeTrace.user_id == user_id)
    if type:
        if not has_type:
            raise HTTPException(
                status_code=400, detail="Filtering by type is not supported"
            )
        stmt = stmt.where(NodeTrace.type == type)
    if source:
        if not has_source:
            raise HTTPException(
                status_code=400, detail="Filtering by source is not supported"
            )
        stmt = stmt.where(NodeTrace.source == source)
    if channel:
        if not has_channel:
            raise HTTPException(
                status_code=400, detail="Filtering by channel is not supported"
            )
        stmt = stmt.where(NodeTrace.channel == channel)
    if date_from and hasattr(NodeTrace, "created_at"):
        stmt = stmt.where(NodeTrace.created_at >= date_from)
    if date_to and hasattr(NodeTrace, "created_at"):
        stmt = stmt.where(NodeTrace.created_at <= date_to)

    if hasattr(NodeTrace, "created_at"):
        stmt = stmt.order_by(NodeTrace.created_at.desc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    try:
        result = await db.execute(stmt)
        rows = result.all()
    except Exception as err:
        logger.exception("Failed to fetch traces: %s", err)
        raise HTTPException(status_code=500, detail="Failed to fetch traces")

    data = []
    for r in rows:
        m = r._mapping
        data.append(
            {
                "id": m["id"],
                "from_slug": m["from_slug"],
                "to_slug": m.get("to_slug"),
                "user_id": m.get("user_id"),
                "source": m.get("source"),
                "channel": m.get("channel"),
                "created_at": m.get("created_at"),
                "type": m.get("type"),
                "latency_ms": m.get("latency_ms"),
                "request_id": m.get("request_id"),
            }
        )

    return data


@router.post("/{trace_id}/anonymize", summary="Anonymize trace (remove user reference)")
async def anonymize_trace(
    trace_id: UUID,
    current_user: Annotated[User, Depends(admin_only)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    trace = await db.get(NodeTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    if hasattr(trace, "user_id"):
        trace.user_id = None
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="anonymize_trace",
        resource_type="trace",
        resource_id=str(trace_id),
    )
    return {"status": "ok"}


@router.delete("/{trace_id}", summary="Delete trace")
async def delete_trace(
    trace_id: UUID,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    trace = await db.get(NodeTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    await db.delete(trace)
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="delete_trace",
        resource_type="trace",
        resource_id=str(trace_id),
    )
    return {"status": "deleted"}


@router.post("/bulk/anonymize", summary="Bulk anonymize traces")
async def bulk_anonymize_traces(
    payload: BulkIds,
    current_user: Annotated[User, Depends(admin_only)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    if not payload.ids:
        return {"updated": 0}
    result = await db.execute(select(NodeTrace).where(NodeTrace.id.in_(payload.ids)))
    traces = result.scalars().all()
    updated = 0
    for t in traces:
        if hasattr(t, "user_id"):
            t.user_id = None
            updated += 1
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="bulk_anonymize_traces",
        resource_type="trace",
        resource_id=",".join(str(i) for i in payload.ids),
    )
    return {"updated": updated}


@router.post("/bulk/delete", summary="Bulk delete traces")
async def bulk_delete_traces(
    payload: BulkIds,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    if not payload.ids:
        return {"deleted": 0}
    result = await db.execute(select(NodeTrace).where(NodeTrace.id.in_(payload.ids)))
    traces = result.scalars().all()
    deleted = 0
    for t in traces:
        await db.delete(t)
        deleted += 1
    await db.commit()
    await log_admin_action(
        db,
        actor_id=current_user.id,
        action="bulk_delete_traces",
        resource_type="trace",
        resource_id=",".join(str(i) for i in payload.ids),
    )
    return {"deleted": deleted}
