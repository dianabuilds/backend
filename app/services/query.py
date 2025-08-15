from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID
import hashlib
import json

from pydantic import BaseModel, Field, validator
from sqlalchemy import func, select, or_, and_
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node
from app.models.transition import NodeTransition, NodeTransitionType
from app.models.tag import Tag
from app.models.user import User
from app.engine.filters import has_access_async


class PageRequest(BaseModel):
    """Simple pagination request."""

    limit: int = 100
    offset: int = 0


class QueryContext(BaseModel):
    """Information about the current user/role for visibility policies."""

    user: Optional[User] = None
    is_admin: bool = False

    class Config:
        arbitrary_types_allowed = True


class NodeFilterSpec(BaseModel):
    author: Optional[UUID] = None
    tags: Optional[List[str]] = None
    match: str = Field("any", pattern="^(any|all)$")
    is_public: Optional[bool] = None
    premium_only: Optional[bool] = None
    recommendable: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    q: Optional[str] = None

    @validator("q")
    def _normalize_q(cls, v: Optional[str]) -> Optional[str]:
        return v.lower() if v else v


class TransitionFilterSpec(BaseModel):
    from_slug: Optional[str] = Field(None, alias="from")
    to_slug: Optional[str] = Field(None, alias="to")
    type: Optional[NodeTransitionType] = None
    author: Optional[UUID] = None


class NodeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def build_query(self, spec: NodeFilterSpec, ctx: QueryContext):
        stmt = select(Node).options(selectinload(Node.tags))

        if not ctx.is_admin:
            conditions = [Node.is_visible == True]  # noqa: E712
            if ctx.user:
                conditions.append(
                    or_(Node.is_public == True, Node.author_id == ctx.user.id)  # noqa: E712
                )
            else:
                conditions.append(Node.is_public == True)  # noqa: E712
            stmt = stmt.where(and_(*conditions))

        if spec.author:
            stmt = stmt.where(Node.author_id == spec.author)
        if spec.is_public is not None:
            stmt = stmt.where(Node.is_public == spec.is_public)
        if spec.premium_only is not None:
            stmt = stmt.where(Node.premium_only == spec.premium_only)
        if spec.recommendable is not None:
            stmt = stmt.where(Node.is_recommendable == spec.recommendable)
        if spec.date_from:
            stmt = stmt.where(Node.updated_at >= spec.date_from)
        if spec.date_to:
            stmt = stmt.where(Node.updated_at <= spec.date_to)
        if spec.q:
            like = f"%{spec.q}%"
            stmt = stmt.where(
                or_(
                    func.lower(Node.title).like(like),
                    func.lower(Node.slug).like(like),
                )
            )
        if spec.tags:
            stmt = stmt.join(Node.tags).where(Tag.slug.in_(spec.tags))
            if spec.match == "all":
                stmt = stmt.group_by(Node.id).having(func.count(Tag.id) == len(spec.tags))
            else:
                stmt = stmt.distinct()
        stmt = stmt.order_by(Node.updated_at.desc())
        return stmt


class TransitionRepository:
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


class NodeQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = NodeRepository(session)

    async def list_nodes(self, spec: NodeFilterSpec, page: PageRequest, ctx: QueryContext):
        stmt = self.repo.build_query(spec, ctx)
        if page:
            stmt = stmt.offset(page.offset).limit(page.limit)
        result = await self.repo.session.execute(stmt)
        nodes = result.scalars().all()
        if not ctx.is_admin:
            user = ctx.user
            filtered: List[Node] = []
            for n in nodes:
                if await has_access_async(n, user):
                    filtered.append(n)
            nodes = filtered
        return nodes

    async def compute_nodes_etag(self, spec: NodeFilterSpec, ctx: QueryContext, page: Optional[PageRequest] = None) -> str:
        """Compute a weak ETag based on spec/context and max(updated_at) for matching nodes.
        Includes pagination parameters to avoid cross-page ETag collisions.
        """
        # Base params that affect visibility and list composition
        params = {
            "spec": spec.model_dump(exclude_none=True),
            "is_admin": ctx.is_admin,
            "user_id": str(ctx.user.id) if ctx.user else None,
            "page": {"limit": page.limit, "offset": page.offset} if page else None,
        }
        # Build filtered query and convert to subquery selecting only updated_at
        base_stmt = self.repo.build_query(spec, ctx)
        subq = base_stmt.with_only_columns(Node.updated_at).order_by(None).subquery()
        res = await self.repo.session.execute(select(func.max(subq.c.updated_at)))
        max_updated = res.scalar()
        payload = {"params": params, "max": max_updated.isoformat() if max_updated else None}
        etag = "W/\"" + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest() + "\""
        return etag

    async def get_node(self, node_id: UUID, ctx: QueryContext) -> Optional[Node]:
        stmt = self.repo.build_query(NodeFilterSpec(), ctx).where(Node.id == node_id)
        result = await self.repo.session.execute(stmt)
        node = result.scalars().first()
        if node and (ctx.is_admin or await has_access_async(node, ctx.user)):
            return node
        return None

    async def get_node_by_slug(self, slug: str, ctx: QueryContext) -> Optional[Node]:
        stmt = self.repo.build_query(NodeFilterSpec(), ctx).where(Node.slug == slug)
        result = await self.repo.session.execute(stmt)
        node = result.scalars().first()
        if node and (ctx.is_admin or await has_access_async(node, ctx.user)):
            return node
        return None

    async def get_node_by_slug_for_view(self, slug: str) -> Optional[Node]:
        """Fetch a node by slug for detail view, ignoring public filter but requiring visibility.
        Authorization (403) is handled by policies at the controller level to preserve current contracts.
        """
        result = await self.repo.session.execute(
            select(Node).options(selectinload(Node.tags)).where(Node.slug == slug, Node.is_visible == True)  # noqa: E712
        )
        return result.scalars().first()


class TransitionQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TransitionRepository(session)

    async def list_transitions(self, spec: TransitionFilterSpec, page: PageRequest, ctx: QueryContext):
        stmt = self.repo.build_query(spec)
        if page:
            stmt = stmt.offset(page.offset).limit(page.limit)
        result = await self.repo.session.execute(stmt)
        return result.all()

    async def compute_transitions_etag(self, spec: TransitionFilterSpec, ctx: QueryContext, page: Optional[PageRequest] = None) -> str:
        """Compute a weak ETag based on spec and max(created_at) for matching transitions."""
        params = {
            "spec": spec.model_dump(exclude_none=True),
            "is_admin": ctx.is_admin,
            "user_id": str(ctx.user.id) if ctx.user else None,
            "page": {"limit": page.limit, "offset": page.offset} if page else None,
        }
        base_stmt = self.repo.build_query(spec)
        subq = (
            base_stmt.with_only_columns(NodeTransition.created_at).order_by(None).subquery()
        )
        res = await self.repo.session.execute(select(func.max(subq.c.created_at)))
        max_created = res.scalar()
        payload = {"params": params, "max": max_created.isoformat() if max_created else None}
        etag = "W/\"" + hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest() + "\""
        return etag

    async def get_transition(self, transition_id: UUID) -> Optional[NodeTransition]:
        result = await self.repo.session.execute(
            select(NodeTransition).where(NodeTransition.id == transition_id)
        )
        return result.scalars().first()
