from __future__ import annotations

import hashlib
import json

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache as shared_cache
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem
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
            clauses.append(Node.is_visible)
        if spec.premium_only is not None and hasattr(Node, "premium_only"):
            clauses.append(Node.premium_only == bool(spec.premium_only))
        if spec.recommendable is not None and hasattr(Node, "is_recommendable"):
            clauses.append(Node.is_recommendable == bool(spec.recommendable))
        if spec.author_id is not None:
            clauses.append(Node.author_id == spec.author_id)
        if spec.workspace_id is not None:
            clauses.append(Node.workspace_id == spec.workspace_id)
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
            clauses.append(Node.title.ilike(pattern))
        if spec.min_views and hasattr(Node, "views"):
            clauses.append(Node.views >= int(spec.min_views))
        base = base.where(and_(*clauses))
        res = await self._db.execute(base)
        cnt, max_updated = (0, None)
        try:
            cnt, max_updated = res.first()
        except Exception:
            pass
        uid = getattr(getattr(ctx, "user", None), "id", None)
        sort = getattr(spec, "sort", "updated_desc") or "updated_desc"
        payload = (
            f"{cnt}:{uid or 'anon'}:{page.offset}:{page.limit}:"
            f"{sort}:{max_updated or ''}:"
            f"{spec.author_id or ''}:{spec.q or ''}:{spec.min_views or ''}:"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    async def list_nodes(
        self, spec: NodeFilterSpec, page: PageRequest, ctx: QueryContext
    ) -> list[Node]:
        stmt = select(Node).join(
            NodeItem,
            and_(NodeItem.node_id == Node.id, NodeItem.status == Status.published),
            isouter=True,
        )
        clauses = []
        if spec.is_visible is not None:
            clauses.append(Node.is_visible == bool(spec.is_visible))
        elif not getattr(ctx, "is_admin", False):
            # Для не-админов по умолчанию показываем только видимые записи
            clauses.append(Node.is_visible)
        if spec.premium_only is not None and hasattr(Node, "premium_only"):
            clauses.append(Node.premium_only == bool(spec.premium_only))
        if spec.recommendable is not None and hasattr(Node, "is_recommendable"):
            clauses.append(Node.is_recommendable == bool(spec.recommendable))
        if spec.author_id is not None:
            clauses.append(Node.author_id == spec.author_id)
        if spec.workspace_id is not None:
            clauses.append(Node.workspace_id == spec.workspace_id)
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
            clauses.append(Node.title.ilike(pattern))
        if spec.min_views and hasattr(Node, "views"):
            clauses.append(Node.views >= int(spec.min_views))
        stmt = stmt.where(and_(*clauses))
        sort = getattr(spec, "sort", "updated_desc") or "updated_desc"
        if sort == "created_desc":
            stmt = stmt.order_by(desc(Node.created_at))
        elif sort == "created_asc":
            stmt = stmt.order_by(asc(Node.created_at))
        elif sort == "views_desc" and hasattr(Node, "views"):
            stmt = stmt.order_by(desc(Node.views))
        else:
            stmt = stmt.order_by(desc(Node.updated_at))
        stmt = stmt.offset(getattr(page, "offset", 0)).limit(getattr(page, "limit", 50))
        res = await self._db.execute(stmt)
        return list(res.scalars().all())

    async def list_drafts_with_issues(self, limit: int = 10) -> list[dict]:
        cache_key = f"admin:drafts:issues:{limit}"
        cached = await shared_cache.get(cache_key)
        if cached:
            return json.loads(cached)
        stmt = (
            select(Node)
            .where(Node.status == Status.draft)
            .order_by(desc(Node.updated_at))
            .limit(limit)
        )
        res = await self._db.execute(stmt)
        nodes = list(res.scalars().all())
        items: list[dict] = []
        for node in nodes:
            issues: list[str] = []
            if not node.title or not node.title.strip():
                issues.append("title")
            items.append(
                {
                    "id": str(node.id),
                    "slug": node.slug,
                    "title": node.title,
                    "issues": issues,
                }
            )
        await shared_cache.set(cache_key, json.dumps(items), 120)
        return items
