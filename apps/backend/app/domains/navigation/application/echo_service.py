from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.infrastructure.models.echo_models import EchoTrace
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTrace
from app.domains.users.infrastructure.models.user import User
from app.domains.navigation.application.access_policy import has_access_async
from app.core.preview import PreviewContext


class EchoService:
    async def record_echo_trace(
        self,
        db: AsyncSession,
        from_node: Node,
        to_node: Node,
        user: Optional[User],
        *,
        source: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> None:
        trace = EchoTrace(
            from_node_id=from_node.id,
            to_node_id=to_node.id,
            user_id=user.id if user and user.is_premium else None,
            source=source,
            channel=channel,
        )
        db.add(trace)
        await db.commit()

    async def get_echo_transitions(
        self,
        db: AsyncSession,
        node: Node,
        limit: int = 3,
        *,
        user: Optional[User] = None,
        preview: PreviewContext | None = None,
    ) -> List[Node]:
        base_now = preview.now if preview and preview.now else datetime.utcnow()
        cutoff = base_now - timedelta(days=30)
        result = await db.execute(
            select(EchoTrace).where(
                EchoTrace.from_node_id == node.id,
                EchoTrace.created_at >= cutoff,
            )
        )
        traces = result.scalars().all()
        counter: Counter = Counter()
        for tr in traces:
            counter[str(tr.to_node_id)] += 1
        if not counter:
            return []
        node_ids = [uuid.UUID(node_id) for node_id in counter.keys()]
        trace_result = await db.execute(
            select(NodeTrace.node_id, func.count())
            .where(NodeTrace.node_id.in_(node_ids))
            .group_by(NodeTrace.node_id)
        )
        for nid, tcount in trace_result.all():
            counter[str(nid)] += tcount
        ordered_nodes: List[Node] = []
        for node_id, _ in counter.most_common(20):
            n = await db.get(Node, uuid.UUID(node_id))
            if not n or not await has_access_async(n, user, preview):
                continue
            ordered_nodes.append(n)
            if len(ordered_nodes) >= limit:
                break
        return ordered_nodes
