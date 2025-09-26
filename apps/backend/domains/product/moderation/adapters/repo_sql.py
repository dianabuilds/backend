from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.moderation.application.ports import Repo
from packages.core.db import get_async_engine


class SQLModerationRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("product-moderation", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def list_cases(
        self, *, page: int, size: int, statuses: Sequence[str] | None = None
    ) -> dict:
        page = max(1, int(page or 1))
        size = max(1, min(int(size or 20), 200))
        offs = (page - 1) * size
        where = ""
        params: dict[str, object] = {}
        if statuses:
            norm = [str(s).lower() for s in statuses]
            where = "WHERE lower(status) = ANY(:st)"
            params["st"] = norm
        q_items = text(
            "SELECT id::text AS id, status, data FROM moderation_cases "
            + where
            + " ORDER BY created_at DESC LIMIT :lim OFFSET :off"
        )
        q_total = text("SELECT count(*)::int AS c FROM moderation_cases " + where)
        async with self._engine.begin() as conn:
            rows = (
                (await conn.execute(q_items, {**params, "lim": size, "off": offs})).mappings().all()
            )
            total = (await conn.execute(q_total, params)).mappings().first().get("c") or 0
        items = []
        for r in rows:
            d = dict(r["data"] or {})
            d["id"] = str(r["id"])  # type: ignore[assignment]
            d["status"] = r["status"]
            items.append(d)
        return {"items": items, "total": int(total), "page": page, "size": size}

    async def create_case(self, payload: dict) -> str:
        sql = text(
            "INSERT INTO moderation_cases(data, status) VALUES (:d, :st) RETURNING id::text AS id"
        )
        st = str(payload.get("status") or "open")
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"d": dict(payload), "st": st})).mappings().first()
            assert r is not None
            return str(r["id"])  # type: ignore[return-value]

    async def add_note(self, case_id: str, note: dict, *, author_id: str | None) -> dict | None:
        chk = text("SELECT 1 FROM moderation_cases WHERE id = cast(:id as uuid)")
        ins = text(
            "INSERT INTO moderation_notes(case_id, author_id, data) VALUES (cast(:cid as uuid), cast(:aid as uuid), :d) RETURNING id::text AS id"
        )
        async with self._engine.begin() as conn:
            ok = (await conn.execute(chk, {"id": case_id})).first()
            if not ok:
                return None
            r = (
                (await conn.execute(ins, {"cid": case_id, "aid": author_id, "d": dict(note)}))
                .mappings()
                .first()
            )
            assert r is not None
            return {"id": str(r["id"]), **dict(note), "author_id": author_id}


__all__ = ["SQLModerationRepo"]
