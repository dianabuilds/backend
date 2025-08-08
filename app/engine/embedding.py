from __future__ import annotations

import hashlib
import os
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.node import Node

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))


def _extract_text(node: Node) -> str:
    parts = []
    if node.title:
        parts.append(node.title)
    if node.content is not None:
        parts.append(str(node.content))
    parts.extend(node.tag_slugs)
    return " ".join(parts)


def simple_embedding(text: str) -> List[float]:
    tokens = text.lower().split()
    vec = [0.0] * EMBEDDING_DIM
    for tok in tokens:
        h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
        idx = h % EMBEDDING_DIM
        vec[idx] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    if norm:
        vec = [v / norm for v in vec]
    return vec


async def update_node_embedding(db: AsyncSession, node: Node) -> None:
    """Compute and store embedding for a node."""
    text = _extract_text(node)
    node.embedding_vector = simple_embedding(text)
    await db.commit()
    await db.refresh(node)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
