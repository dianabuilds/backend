from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api.deps import get_current_user_optional
from app.db.session import get_db
from app.engine.embedding import get_embedding, cosine_similarity
from app.engine.filters import has_access_async
from app.repositories.compass_repository import CompassRepository
from app.core.config import settings
from app.models.node import Node
from app.models.tag import Tag
from app.models.user import User

router = APIRouter(tags=["search"])


@router.get("/search")
async def search_nodes(
    q: str | None = None,
    tags: str | None = Query(None),
    match: str = Query("any", pattern="^(any|all)$"),
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    stmt = select(Node).where(Node.is_visible == True)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Node.title.ilike(pattern))
    if tags:
        slugs = [t.strip() for t in tags.split(",") if t.strip()]
        if slugs:
            stmt = stmt.join(Node.tags).where(Tag.slug.in_(slugs))
            if match == "all":
                stmt = stmt.group_by(Node.id).having(func.count(Tag.id) == len(slugs))
            else:
                stmt = stmt.distinct()
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    nodes = result.scalars().all()
    filtered = [n for n in nodes if await has_access_async(n, user)]
    return [
        {"slug": n.slug, "title": n.title, "tags": n.tag_slugs, "score": 1.0}
        for n in filtered
    ]


@router.get("/search/semantic")
async def semantic_search(
    q: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    """Semantic search using vector similarity."""
    query_vec = get_embedding(q)
    repo = CompassRepository(db)
    candidates = await repo.search_by_vector_pgvector(
        query_vec, limit, settings.compass.pgv_probes
    )
    results: list[tuple[Node, float]] = []
    if candidates is None:
        stmt = select(Node).where(
            Node.is_visible == True,
            Node.is_public == True,
            Node.is_recommendable == True,
            Node.embedding_vector.isnot(None),
        )
        nodes = (await db.execute(stmt)).scalars().all()
        for n in nodes:
            if not await has_access_async(n, user):
                continue
            score = cosine_similarity(query_vec, n.embedding_vector)
            results.append((n, score))
        results.sort(key=lambda x: x[1], reverse=True)
    else:
        for n, dist in candidates:
            if not await has_access_async(n, user):
                continue
            results.append((n, 1 - dist))

    return [
        {
            "slug": n.slug,
            "title": n.title,
            "tags": n.tag_slugs,
            "score": float(round(s, 4)),
        }
        for n, s in results[:limit]
    ]
