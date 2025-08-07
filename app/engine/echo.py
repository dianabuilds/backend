from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node
from app.models.echo_trace import EchoTrace
from app.models.user import User


async def record_echo_trace(
    db: AsyncSession, from_node: Node, to_node: Node, user: User | None
) -> None:
    trace = EchoTrace(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        user_id=user.id if user and user.is_premium else None,
    )
    db.add(trace)
    await db.commit()


async def get_echo_transitions(
    db: AsyncSession, node: Node, limit: int = 3
) -> List[Node]:
    cutoff = datetime.utcnow() - timedelta(days=30)
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
    ordered_nodes: List[Node] = []
    for node_id, _ in counter.most_common(20):
        n = await db.get(Node, uuid.UUID(node_id))
        if not n or not n.is_visible or not n.is_public:
            continue
        ordered_nodes.append(n)
        if len(ordered_nodes) >= limit:
            break
    return ordered_nodes
