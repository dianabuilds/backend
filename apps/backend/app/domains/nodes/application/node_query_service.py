from __future__ import annotations

import hashlib

from sqlalchemy import String, and_, asc, cast, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
from app.domains.tags.models import Tag
from app.schemas.nodes_common import Status


class NodeQueryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def compute_nodes_etag(
        self, spec: NodeFilterSpec, ctx: QueryContext, page: PageRequest
    ) -> str:
        base = select(
            func.coalesce(func.count(Node.id), 0), func.max(Node.updated_at)
        ).join(
            NodeItem,
            and_(NodeItem.node_id == Node.id, NodeItem.status == Status.published),
            isouter=True,
        )
        clauses = []
        if spec.is_visible is not None:
            clauses.append(Node.is_visible == bool(spec.is_visible))
        elif not getattr(ctx, "is_admin", False):
            # Для не-админов по умолчанию показываем только видимые записи
            clauses.append(Node.is_visible == True)  # noqa: E712
        if spec.is_public is not None:
            clauses.append(Node.is_public == bool(spec.is_public))
        if spec.premium_only is not None and hasattr(Node, "premium_only"):
            clauses.append(Node.premium_only == bool(spec.premium_only))
        if spec.recommendable is not None and hasattr(Node, "is_recommendable"):
            clauses.append(Node.is_recommendable == bool(spec.recommendable))
        if spec.author_id is not None:
            clauses.append(Node.author_id == spec.author_id)
        if spec.workspace_id is not None:
            clauses.append(Node.workspace_id == spec.workspace_id)
        if spec.node_type is not None:
            clauses.append(NodeItem.type == spec.node_type)
        if spec.created_from:
            clauses.append(Node.created_at >= spec.created_from)
        if spec.created_to:
            clauses.append(Node.created_at <= spec.created_to)
        if spec.updated_from:
            clauses.append(Node.updated_at >= spec.updated_from)
        if spec.updated_to:
            clauses.append(Node.updated_at <= spec.updated_to)
        if spec.q:
            pattern = f"%{spec.q.strip()}%"
            clauses.append(
                or_(
                    Node.title.ilike(pattern), cast(Node.content, String).ilike(pattern)
                )
            )
        if spec.min_views and hasattr(Node, "views"):
            clauses.append(Node.views >= int(spec.min_views))
        if spec.min_reactions and hasattr(Node, "reactions"):
            clauses.append(Node.reactions >= int(spec.min_reactions))
        base = base.where(and_(*clauses))
        if spec.tags:
            base = base.join(Node.tags).where(Tag.slug.in_(spec.tags))
            if spec.match == "all":
                base = base.group_by(Node.id).having(
                    func.count(Tag.id) == len(spec.tags)
                )
        res = await self._db.execute(base)
        cnt, max_updated = (0, None)
        try:
            cnt, max_updated = res.first()
        except Exception:
            pass
        uid = getattr(getattr(ctx, "user", None), "id", None)
        sort = getattr(spec, "sort", "updated_desc") or "updated_desc"
        payload = (
            f"{cnt}:{uid or 'anon'}:{spec.tags or []}:{spec.match}:"
            f"{page.offset}:{page.limit}:{sort}:{max_updated or ''}:"
            f"{spec.author_id or ''}:{spec.q or ''}:{spec.min_views or ''}:"
            f"{spec.min_reactions or ''}:{spec.node_type or ''}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    async def list_nodes(
        self, spec: NodeFilterSpec, page: PageRequest, ctx: QueryContext
    ) -> list[Node]:
        stmt = select(Node, NodeItem.type.label("node_type")).join(
            NodeItem,
            and_(NodeItem.node_id == Node.id, NodeItem.status == Status.published),
            isouter=True,
        )
        clauses = []
        if spec.is_visible is not None:
            clauses.append(Node.is_visible == bool(spec.is_visible))
        elif not getattr(ctx, "is_admin", False):
            # Для не-админов по умолчанию показываем только видимые записи
            clauses.append(Node.is_visible == True)  # noqa: E712
        if spec.is_public is not None:
            clauses.append(Node.is_public == bool(spec.is_public))
        if spec.premium_only is not None and hasattr(Node, "premium_only"):
            clauses.append(Node.premium_only == bool(spec.premium_only))
        if spec.recommendable is not None and hasattr(Node, "is_recommendable"):
            clauses.append(Node.is_recommendable == bool(spec.recommendable))
        if spec.author_id is not None:
            clauses.append(Node.author_id == spec.author_id)
        if spec.workspace_id is not None:
            clauses.append(Node.workspace_id == spec.workspace_id)
        if spec.node_type is not None:
            clauses.append(NodeItem.type == spec.node_type)
        if spec.created_from:
            clauses.append(Node.created_at >= spec.created_from)
        if spec.created_to:
            clauses.append(Node.created_at <= spec.created_to)
        if spec.updated_from:
            clauses.append(Node.updated_at >= spec.updated_from)
        if spec.updated_to:
            clauses.append(Node.updated_at <= spec.updated_to)
        if spec.q:
            pattern = f"%{spec.q.strip()}%"
            clauses.append(
                or_(
                    Node.title.ilike(pattern), cast(Node.content, String).ilike(pattern)
                )
            )
        if spec.min_views and hasattr(Node, "views"):
            clauses.append(Node.views >= int(spec.min_views))
        if spec.min_reactions and hasattr(Node, "reactions"):
            clauses.append(Node.reactions >= int(spec.min_reactions))
        stmt = stmt.where(and_(*clauses))
        if spec.tags:
            stmt = stmt.join(Node.tags).where(Tag.slug.in_(spec.tags))
            if spec.match == "all":
                stmt = stmt.group_by(Node.id).having(
                    func.count(Tag.id) == len(spec.tags)
                )
            else:
                stmt = stmt.distinct()
        sort = getattr(spec, "sort", "updated_desc") or "updated_desc"
        if sort == "created_desc":
            stmt = stmt.order_by(desc(Node.created_at))
        elif sort == "created_asc":
            stmt = stmt.order_by(asc(Node.created_at))
        elif sort == "views_desc" and hasattr(Node, "views"):
            stmt = stmt.order_by(desc(Node.views))
        elif sort == "reactions_desc" and hasattr(Node, "reactions"):
            stmt = stmt.order_by(desc(Node.reactions))
        else:
            stmt = stmt.order_by(desc(Node.updated_at))
        stmt = stmt.offset(getattr(page, "offset", 0)).limit(getattr(page, "limit", 50))
        res = await self._db.execute(stmt)
        items: list[Node] = []
        for node, node_type in res.all():
            node.node_type = node_type
            items.append(node)
        return items

    async def list_drafts_with_issues(
        self, limit: int = 10
    ) -> list[tuple[Node, list[str]]]:
        stmt = (
            select(Node)
            .options(selectinload(Node.tags))
            .where(
                Node.status == Status.draft,
                or_(
                    Node.cover_url.is_(None),
                    func.coalesce(func.length(func.trim(Node.title)), 0) == 0,
                    ~Node.tags.any(),
                ),
            )
            .order_by(desc(Node.updated_at))
            .limit(limit)
        )
        res = await self._db.execute(stmt)
        nodes = list(res.scalars().unique().all())
        items: list[tuple[Node, list[str]]] = []
        for node in nodes:
            issues: list[str] = []
            if not node.cover_url:
                issues.append("cover")
            if not node.title or not node.title.strip():
                issues.append("title")
            if not getattr(node, "tags", []):
                issues.append("tags")
            items.append((node, issues))
        return items
