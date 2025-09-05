from __future__ import annotations

from typing import Any, Protocol

from app.schemas.node import NodeOut


class INodeQueryService(Protocol):
    async def compute_nodes_etag(self, spec: Any, ctx: Any, page: Any) -> str:  # pragma: no cover
        ...

    async def list_nodes(self, spec: Any, page: Any, ctx: Any) -> list[NodeOut]:  # pragma: no cover
        ...
