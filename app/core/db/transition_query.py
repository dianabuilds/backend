from __future__ import annotations

import hashlib
import json
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTransition, NodeTransitionType
from app.domains.nodes.application.query_models import PageRequest, QueryContext

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTransition, NodeTransitionType
from app.domains.nodes.application.query_models import PageRequest, QueryContext


class TransitionFilterSpec(BaseModel):
    from_slug: Optional[str] = Field(None, alias="from")
    to_slug: Optional[str] = Field(None, alias="to")
    type: Optional[NodeTransitionType] = None
    author: Optional[NodeTransition.created_by.type] = None  # type: ignore[attr-defined]


class TransitionQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _build_query(self, spec: TransitionFilterSpec):
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
        self, spec: TransitionFilterSpec, page: PageRequest, ctx: QueryContext
    ):
        stmt = self._build_query(spec)
        if page:
            stmt = stmt.offset(page.offset).limit(page.limit)
        result = await self.session.execute(stmt)
        return result.all()

    async def compute_transitions_etag(
        self, spec: TransitionFilterSpec, ctx: QueryContext, page: Optional[PageRequest] = None
    ) -> str:
        """
        Вычисляет weak ETag по максимуму created_at среди переходов,
        с учётом фильтров и параметров пагинации.
        """
        base_stmt = self._build_query(spec)
        subq = base_stmt.with_only_columns(NodeTransition.created_at).order_by(None).subquery()
        res = await self.session.execute(select(func.max(subq.c.created_at)))
        max_created = res.scalar()
        # Простая стабильная схема формирования слабого ETag:
        # учитываем фильтры + максимум created_at + пагинацию
        import hashlib, json
        payload = {
            "spec": spec.model_dump(exclude_none=True),
            "is_admin": ctx.is_admin,
            "user_id": str(getattr(ctx.user, "id", "")) if ctx.user else None,
            "page": {"limit": page.limit, "offset": page.offset} if page else None,
            "max": max_created.isoformat() if max_created else None,
        }
        etag = 'W/"' + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest() + '"'
        return etag
class TransitionFilterSpec(BaseModel):
    from_slug: Optional[str] = Field(None, alias="from")
    to_slug: Optional[str] = Field(None, alias="to")
    type: Optional[NodeTransitionType] = None
    author: Optional[UUID] = None


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

    async def list_transitions(self, spec: TransitionFilterSpec, page: PageRequest, _ctx: QueryContext):
        stmt = self.build_query(spec)
        if page:
            stmt = stmt.offset(page.offset).limit(page.limit)
        result = await self.session.execute(stmt)
        return result.all()
from __future__ import annotations

import hashlib
import json
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTransition, NodeTransitionType
from app.domains.nodes.application.query_models import PageRequest, QueryContext


class TransitionFilterSpec(BaseModel):
    from_slug: Optional[str] = Field(None, alias="from")
    to_slug: Optional[str] = Field(None, alias="to")
    type: Optional[NodeTransitionType] = None
    author: Optional[UUID] = None


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

    async def list_transitions(self, spec: TransitionFilterSpec, page: PageRequest, _ctx: QueryContext):
        stmt = self.build_query(spec)
        if page:
            stmt = stmt.offset(page.offset).limit(page.limit)
        result = await self.session.execute(stmt)
        return result.all()

    async def compute_transitions_etag(
        self,
        spec: TransitionFilterSpec,
        _ctx: QueryContext,
        page: Optional[PageRequest] = None,
    ) -> str:
        """Compute a weak ETag based on spec and max(created_at) for matching transitions."""
        params = {
            "spec": spec.model_dump(exclude_none=True),
            "page": {"limit": page.limit, "offset": page.offset} if page else None,
        }
        base_stmt = self.build_query(spec)
        subq = base_stmt.with_only_columns(NodeTransition.created_at).order_by(None).subquery()
        res = await self.session.execute(select(func.max(subq.c.created_at)))
        max_created = res.scalar()
        payload = {"params": params, "max": max_created.isoformat() if max_created else None}
        etag = 'W/"' + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest() + '"'
        return etag
    async def compute_transitions_etag(
        self,
        spec: TransitionFilterSpec,
        _ctx: QueryContext,
        page: Optional[PageRequest] = None,
    ) -> str:
        """Compute a weak ETag based on spec and max(created_at) for matching transitions."""
        params = {
            "spec": spec.model_dump(exclude_none=True),
            "page": {"limit": page.limit, "offset": page.offset} if page else None,
        }
        base_stmt = self.build_query(spec)
        subq = base_stmt.with_only_columns(NodeTransition.created_at).order_by(None).subquery()
        res = await self.session.execute(select(func.max(subq.c.created_at)))
        max_created = res.scalar()
        payload = {"params": params, "max": max_created.isoformat() if max_created else None}
        etag = 'W/"' + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest() + '"'
        return etag
