from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.engine.compass import get_compass_nodes
from app.engine.echo import get_echo_transitions
from app.engine.random import get_random_node
from app.engine.filters import has_access_async
from app.engine.transitions import get_transitions
from app.models.node import Node
from app.models.user import User
from app.services.navcache import navcache


def _normalise(scores: List[Node]) -> dict[str, float]:
    """Return a mapping slug->score in range 0..1 based on order."""
    if not scores:
        return {}
    size = len(scores)
    return {n.slug: 1 - i / size for i, n in enumerate(scores)}


async def generate_transitions(
    db: AsyncSession, node: Node, user: Optional[User]
) -> List[Dict[str, object]]:
    """Collect transition candidates from different sources and score them."""

    max_options = settings.navigation_max_options

    # Manual transitions always come first
    manual: List[Dict[str, object]] = []
    for t in await get_transitions(db, node, user):
        if not await has_access_async(t.to_node, user):
            continue
        manual.append(
            {
                "slug": t.to_node.slug,
                "title": t.to_node.title,
                "source_type": t.type.value,
                "score": float(t.weight or 1),
            }
        )

    # Automatic sources
    remaining = max_options
    remaining -= len(manual)
    if remaining <= 0:
        return manual

    compass_nodes = await get_compass_nodes(db, node, user, remaining)
    echo_nodes = await get_echo_transitions(db, node, remaining, user=user)
    rnd = await get_random_node(db, user=user, exclude_node_id=node.id)

    candidates: dict[str, dict[str, object]] = {}

    for source, nodes in {
        "compass": compass_nodes,
        "echo": echo_nodes,
    }.items():
        norm = _normalise(nodes)
        for n in nodes:
            if not await has_access_async(n, user):
                continue
            data = candidates.setdefault(n.slug, {"node": n, "scores": defaultdict(float)})
            data["scores"][source] = norm[n.slug]

    if rnd and await has_access_async(rnd, user):
        data = candidates.setdefault(rnd.slug, {"node": rnd, "scores": defaultdict(float)})
        data["scores"]["random"] = 1.0

    weighted: List[Dict[str, object]] = []
    for slug, data in candidates.items():
        n: Node = data["node"]
        s = data["scores"]
        total = (
            settings.navigation_weight_compass * s.get("compass", 0)
            + settings.navigation_weight_echo * s.get("echo", 0)
            + settings.navigation_weight_random * s.get("random", 0)
        )
        source_type = max(s.items(), key=lambda kv: kv[1])[0]
        weighted.append(
            {
                "slug": slug,
                "title": n.title,
                "source_type": source_type,
                "score": round(float(total), 4),
            }
        )

    weighted.sort(key=lambda x: x["score"], reverse=True)
    seen = {t["slug"] for t in manual}
    automatic = [t for t in weighted if t["slug"] not in seen][: max(0, remaining)]
    return manual + automatic


async def get_navigation(
    db: AsyncSession, node: Node, user: Optional[User]
) -> Dict[str, object]:
    user_key = str(user.id) if user else "anon"
    if settings.enable_nav_cache:
        cached = await navcache.get_navigation(user_key, str(node.id), "auto")
        if cached:
            return cached
    transitions = await generate_transitions(db, node, user)
    data = {
        "mode": "auto",
        "transitions": transitions,
        "generated_at": datetime.utcnow().isoformat(),
    }
    if settings.enable_nav_cache:
        await navcache.set_navigation(user_key, str(node.id), "auto", data)
    return data


async def invalidate_navigation_cache(user: Optional[User], node: Node) -> None:
    await navcache.invalidate_navigation_by_node(str(node.id))


async def invalidate_all_for_node(node: Node) -> None:
    await navcache.invalidate_navigation_by_node(str(node.id))
