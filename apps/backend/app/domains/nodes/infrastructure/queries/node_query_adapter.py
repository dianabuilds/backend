from __future__ import annotations  # mypy: ignore-errors

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.application.ports.node_query_port import INodeQueryService
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)


class NodeQueryAdapter(INodeQueryService):
    def __init__(self, db: AsyncSession) -> None:
        self._svc = NodeQueryService(db)

    async def compute_nodes_etag(
        self, spec: NodeFilterSpec, ctx: QueryContext, page: PageRequest
    ) -> str:
        return await self._svc.compute_nodes_etag(spec, ctx, page)

    async def list_nodes(self, spec: NodeFilterSpec, page: PageRequest, ctx: QueryContext):
        return await self._svc.list_nodes(spec, page, ctx)
