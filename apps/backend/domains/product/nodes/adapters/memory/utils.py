from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class _HasSlug(Protocol):
    def get_by_slug(self, slug: str) -> Any: ...


async def resolve_memory_node(container: Any, node_ref: str) -> Any | None:
    """Lookup a node using in-memory repositories when SQL access is unavailable."""

    service = getattr(container, "nodes_service", None)
    if service is None:
        return None
    repo: object | None = getattr(service, "repo", None)
    dto: Any | None = None
    repo_get = getattr(service, "_repo_get_async", None)
    if callable(repo_get):
        try:
            dto = await repo_get(int(node_ref))
        except (TypeError, ValueError, AttributeError):
            dto = None
    if dto is None and isinstance(repo, _HasSlug):
        try:
            dto = repo.get_by_slug(str(node_ref))
        except Exception:
            dto = None
    return dto


__all__ = ["resolve_memory_node"]
