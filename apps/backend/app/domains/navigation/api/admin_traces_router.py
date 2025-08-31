from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
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
    node_alias = aliased(Node)

    stmt = select(NodeTrace, node_alias.slug).join(
        node_alias, NodeTrace.node_id == node_alias.id
    )

    if from_slug:
        stmt = stmt.where(node_alias.slug == from_slug)
    if user_id and hasattr(NodeTrace, "user_id"):
        stmt = stmt.where(NodeTrace.user_id == user_id)
    if type and hasattr(NodeTrace, "type"):
        stmt = stmt.where(NodeTrace.type == type)
    if source and hasattr(NodeTrace, "source"):
        stmt = stmt.where(NodeTrace.source == source)
    if channel and hasattr(NodeTrace, "channel"):
        stmt = stmt.where(NodeTrace.channel == channel)
    if date_from and hasattr(NodeTrace, "created_at"):
        stmt = stmt.where(NodeTrace.created_at >= date_from)
    if date_to and hasattr(NodeTrace, "created_at"):
        stmt = stmt.where(NodeTrace.created_at <= date_to)

    if hasattr(NodeTrace, "created_at"):
        stmt = stmt.order_by(NodeTrace.created_at.desc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    rows = result.all()

    data = []
    for t, fs in rows:
        item = {
            "id": t.id,
            "from_slug": fs,
            "to_slug": None,
        }
        for field in (
            "user_id",
            "source",
            "channel",
            "created_at",
            "type",
            "latency_ms",
            "request_id",
        ):
            item[field] = getattr(t, field, None)
        data.append(item)

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
