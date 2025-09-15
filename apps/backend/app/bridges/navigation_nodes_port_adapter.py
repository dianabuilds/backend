from __future__ import annotations

from typing import Sequence

from apps.backendDDD.domains.product.nodes.application.service import NodeService


class NodesReadPort:
    def __init__(self, svc: NodeService):
        self._svc = svc

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0) -> Sequence[dict]:
        items = self._svc.list_by_author(author_id, limit=limit, offset=offset)
        return [{"id": x.id, "author_id": x.author_id, "title": x.title, "is_public": x.is_public} for x in items]

    def get(self, node_id: int) -> dict | None:
        view = self._svc.get(node_id)
        if not view:
            return None
        return {"id": view.id, "author_id": view.author_id, "title": view.title, "is_public": view.is_public}
