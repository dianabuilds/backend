from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_query_port import INodeQueryService
from app.domains.nodes.application.query_models import NodeFilterSpec, PageRequest, QueryContext
from app.core.db.query import (
    NodeQueryService as LegacyNodeQueryService,
    NodeFilterSpec as LegacySpec,
    PageRequest as LegacyPage,
    QueryContext as LegacyCtx,
)


class NodeQueryAdapter(INodeQueryService):
    def __init__(self, db: AsyncSession) -> None:
        self._svc = LegacyNodeQueryService(db)

    def _to_legacy(self, spec: NodeFilterSpec, ctx: QueryContext, page: PageRequest):
        lspec = LegacySpec(tags=spec.tags, match=spec.match)
        lctx = LegacyCtx(user=ctx.user, is_admin=ctx.is_admin)
        lpage = LegacyPage()  # используем дефолты legacy, оффсет/лимит задаются внутри сервисов
        setattr(lpage, "offset", getattr(page, "offset", 0))
        setattr(lpage, "limit", getattr(page, "limit", 50))
        return lspec, lctx, lpage

    async def compute_nodes_etag(self, spec: NodeFilterSpec, ctx: QueryContext, page: PageRequest) -> str:
        lspec, lctx, lpage = self._to_legacy(spec, ctx, page)
        return await self._svc.compute_nodes_etag(lspec, lctx, lpage)

    async def list_nodes(self, spec: NodeFilterSpec, page: PageRequest, ctx: QueryContext):
        lspec, lctx, lpage = self._to_legacy(spec, ctx, page)
        return await self._svc.list_nodes(lspec, lpage, lctx)
