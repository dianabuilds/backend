from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backend import get_container
from domains.platform.iam.security import (
    get_current_user,
    require_admin,
)
from packages.core.config import to_async_dsn


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/users", tags=["users"])

    @router.get("/me")
    async def me(req: Request, claims=Depends(get_current_user)) -> dict[str, Any]:
        c = get_container(req)
        user_id = str(claims.get("sub"))
        user = await c.users.service.get(user_id)
        return {"user": (None if not user else user.__dict__)}

    @router.get("/{user_id}")
    async def get_user(
        req: Request, user_id: str, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        user = await c.users.service.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="user_not_found")
        return {"user": user.__dict__}

    async def _ensure_engine(container) -> AsyncEngine | None:
        try:
            dsn = to_async_dsn(container.settings.database_url)
            if not dsn:
                return None
            if "?" in dsn:
                dsn = dsn.split("?", 1)[0]
            return create_async_engine(dsn, future=True)
        except Exception:
            return None

    @router.get("/search")
    async def search_users(
        req: Request,
        q: str = Query(default="", description="Search by username/email (ILIKE)"),
        limit: int = Query(ge=1, le=50, default=20),
        _admin: None = Depends(require_admin),
    ) -> list[dict[str, Any]]:
        c = get_container(req)
        eng = await _ensure_engine(c)
        if eng is None:
            return []
        sql = text(
            """
            SELECT id::text AS id, COALESCE(username, email) AS username
            FROM users
            WHERE (:q = '' OR lower(COALESCE(username, '')) LIKE lower(:qp) OR lower(COALESCE(email, '')) LIKE lower(:qp))
            ORDER BY username NULLS LAST, id ASC
            LIMIT :lim
            """
        )
        async with eng.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        sql,
                        {"q": str(q or ""), "qp": f"%{str(q or '').strip()}%", "lim": int(limit)},
                    )
                )
                .mappings()
                .all()
            )
        return [{"id": str(r["id"]), "username": r.get("username")} for r in rows]

    return router
