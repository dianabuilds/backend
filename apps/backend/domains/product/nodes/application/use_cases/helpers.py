from __future__ import annotations

from fastapi import HTTPException

from domains.product.nodes.application.use_cases.ports import NodesServicePort
from domains.product.nodes.domain.results import NodeView


async def resolve_node_ref(
    service: NodesServicePort, node_ref: str
) -> tuple[NodeView, int]:
    """Resolve node reference (id or slug) to NodeView and numeric id."""
    view: NodeView | None = None
    resolved_id: int | None = None
    maybe_id: int | None = None
    try:
        maybe_id = int(node_ref)
    except (TypeError, ValueError):
        maybe_id = None
    if maybe_id is not None:
        dto = await service._repo_get_async(maybe_id)
        if dto is not None:
            try:
                resolved_id = int(dto.id)
            except (TypeError, ValueError):
                resolved_id = None
            else:
                view = service._to_view(dto)
    if view is None:
        dto = await service._repo_get_by_slug_async(str(node_ref))
        if dto is not None:
            try:
                resolved_id = int(dto.id)
            except (TypeError, ValueError):
                resolved_id = None
            view = service._to_view(dto)
    if view is None or resolved_id is None:
        raise HTTPException(status_code=404, detail="not_found")
    return view, resolved_id
