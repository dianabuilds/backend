from __future__ import annotations

import hashlib
import json
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
    NodeTransitionType,
)
from app.domains.nodes.application.query_models import PageRequest, QueryContext
from app.domains.nodes.infrastructure.models.node import Node


class TransitionFilterSpec(BaseModel):
    from_slug: str | None = Field(None, alias="from")
    to_slug: str | None = Field(None, alias="to")
    type: NodeTransitionType | None = None
    author: UUID | None = None


class TransitionQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def build_query(self, spec: TransitionFilterSpec):
        from_node = aliased(Node)
        to_node = aliased(Node)
        stmt = (
            select(NodeTransition, from_node.slug, to_node.slug)
            .join(from_node, NodeTransition.from_node_id == from_node.id)
            .join(to_node, NodeTransition.to_node_id == to_node.id)
        )
        if spec.from_slug:
            stmt = stmt.where(from_node.slug == spec.from_slug)
        if spec.to_slug:
            stmt = stmt.where(to_node.slug == spec.to_slug)
        if spec.type:
            stmt = stmt.where(NodeTransition.type == spec.type)
        if spec.author:
            stmt = stmt.where(NodeTransition.created_by == spec.author)
        stmt = stmt.order_by(NodeTransition.created_at.desc())
        return stmt

    async def list_transitions(
        self, spec: TransitionFilterSpec, page: PageRequest, _ctx: QueryContext
    ):
        stmt = self.build_query(spec)
        if page:
            stmt = stmt.offset(page.offset).limit(page.limit)
        result = await self.session.execute(stmt)
        return result.all()

    async def compute_transitions_etag(
        self,
        spec: TransitionFilterSpec,
        _ctx: QueryContext,
        page: PageRequest | None = None,
    ) -> str:
        params = {
            "spec": spec.model_dump(exclude_none=True),
            "page": {"limit": page.limit, "offset": page.offset} if page else None,
        }
        base_stmt = self.build_query(spec)
        subq = base_stmt.with_only_columns(NodeTransition.created_at).order_by(None).subquery()
        res = await self.session.execute(select(func.max(subq.c.created_at)))
        max_created = res.scalar()
        payload = {
            "params": params,
            "max": max_created.isoformat() if max_created else None,
        }
        etag = (
            'W/"'
            + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
            + '"'
        )
        return etag


__all__ = [
    "TransitionFilterSpec",
    "TransitionQueryService",
]
