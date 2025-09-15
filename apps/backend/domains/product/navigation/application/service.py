from __future__ import annotations

import random

from domains.product.navigation.application.ports import (
    NextInput,
    NodesPort,
)
from domains.product.navigation.domain.results import NextStep


class NavigationService:
    def __init__(self, nodes: NodesPort):
        self.nodes = nodes

    def next(self, data: NextInput) -> NextStep:
        # Simple baseline: if current provided -> return a different node from same author; else pick any from author
        author_id = data.user_id
        items = list(self.nodes.list_by_author(author_id, limit=100))
        candidates = [
            it for it in items if int(it.get("id")) != int(data.current_node_id or -1)
        ]
        if not candidates:
            return NextStep(node_id=None, reason="no_candidates")
        choice = random.choice(candidates)
        return NextStep(node_id=int(choice.get("id")), reason=data.strategy)
