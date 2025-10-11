from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.quests.application.ports import (
    CreateQuestInput,
    QuestDTO,
    Repo,
)
from packages.core.async_utils import run_sync
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.repository import MemoryQuestsRepo

logger = logging.getLogger(__name__)


class SQLQuestsRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("quests", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def _aload_tags(self, quest_ids: list[str]) -> dict[str, list[str]]:
        if not quest_ids:
            return {}
        sql = text(
            "SELECT quest_id::text AS quest_id, slug FROM quest_tags WHERE quest_id = ANY(:ids) ORDER BY slug"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, {"ids": quest_ids})).mappings().all()
        out: dict[str, list[str]] = {}
        for r in rows:
            qid = str(r["quest_id"])  # type: ignore[redundant-cast]
            out.setdefault(qid, []).append(str(r["slug"]))
        return out

    def get(self, quest_id: str) -> QuestDTO | None:

        async def _run() -> QuestDTO | None:
            sql = text(
                "SELECT id::text AS id, author_id::text AS author_id, slug, title, description, is_public FROM quests WHERE id = cast(:id as uuid)"
            )
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, {"id": str(quest_id)})).mappings().first()
            if not r:
                return None
            tags = await self._aload_tags([str(quest_id)])
            return QuestDTO(
                id=str(r["id"]),
                author_id=str(r["author_id"]),
                slug=str(r["slug"]),
                title=str(r["title"]),
                description=r["description"],
                tags=tags.get(str(quest_id), []),
                is_public=bool(r["is_public"]),
            )

        return run_sync(_run())

    def get_by_slug(self, slug: str) -> QuestDTO | None:

        async def _run() -> QuestDTO | None:
            sql = text(
                "SELECT id::text AS id, author_id::text AS author_id, slug, title, description, is_public FROM quests WHERE slug = :slug"
            )
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, {"slug": str(slug)})).mappings().first()
            if not r:
                return None
            qid = str(r["id"])  # type: ignore[redundant-cast]
            tags = await self._aload_tags([qid])
            return QuestDTO(
                id=qid,
                author_id=str(r["author_id"]),
                slug=str(r["slug"]),
                title=str(r["title"]),
                description=r["description"],
                tags=tags.get(qid, []),
                is_public=bool(r["is_public"]),
            )

        return run_sync(_run())

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[QuestDTO]:

        async def _run() -> list[QuestDTO]:
            sql = text(
                """
                SELECT id::text AS id, author_id::text AS author_id, slug, title, description, is_public
                FROM quests
                WHERE author_id = cast(:aid as uuid)
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
            )
            async with self._engine.begin() as conn:
                rows = (
                    (
                        await conn.execute(
                            sql,
                            {
                                "aid": str(author_id),
                                "limit": int(limit),
                                "offset": int(offset),
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
            ids = [str(r["id"]) for r in rows]
            tagmap = await self._aload_tags(ids)
            out: list[QuestDTO] = []
            for r in rows:
                qid = str(r["id"])  # type: ignore[redundant-cast]
                out.append(
                    QuestDTO(
                        id=qid,
                        author_id=str(r["author_id"]),
                        slug=str(r["slug"]),
                        title=str(r["title"]),
                        description=r["description"],
                        tags=tagmap.get(qid, []),
                        is_public=bool(r["is_public"]),
                    )
                )
            return out

        return run_sync(_run())

    def create(self, data: CreateQuestInput, slug: str) -> QuestDTO:

        async def _run() -> QuestDTO:
            async with self._engine.begin() as conn:
                r = (
                    (
                        await conn.execute(
                            text(
                                """
                            INSERT INTO quests(author_id, slug, title, description, is_public)
                            VALUES (cast(:aid as uuid), :slug, :title, :description, :pub)
                            RETURNING id::text AS id, author_id::text AS author_id, slug, title, description, is_public
                            """
                            ),
                            {
                                "aid": data.author_id,
                                "slug": slug,
                                "title": data.title,
                                "description": data.description,
                                "pub": bool(data.is_public),
                            },
                        )
                    )
                    .mappings()
                    .first()
                )
                if r is None:

                    raise RuntimeError("database_row_missing")
                qid = str(r["id"])  # type: ignore[redundant-cast]
                for s in data.tags or []:
                    v = str(s).strip().lower()
                    if not v:
                        continue
                    await conn.execute(
                        text(
                            "INSERT INTO quest_tags(quest_id, slug) VALUES (cast(:id as uuid), :slug) ON CONFLICT DO NOTHING"
                        ),
                        {"id": qid, "slug": v},
                    )
            got = await self._araw_get(qid)
            if got is None:

                raise RuntimeError("database_row_missing")
            return got

        return run_sync(_run())

    def set_tags(self, quest_id: str, tags: Sequence[str]) -> QuestDTO:

        async def _run() -> QuestDTO:
            norm: list[str] = []
            seen: set[str] = set()
            for s in tags:
                v = str(s).strip().lower()
                if not v or v in seen:
                    continue
                seen.add(v)
                norm.append(v)
            async with self._engine.begin() as conn:
                chk = (
                    await conn.execute(
                        text("SELECT 1 FROM quests WHERE id = cast(:id as uuid)"),
                        {"id": str(quest_id)},
                    )
                ).first()
                if not chk:
                    raise ValueError("quest not found")
                await conn.execute(
                    text("DELETE FROM quest_tags WHERE quest_id = cast(:id as uuid)"),
                    {"id": str(quest_id)},
                )
                for s in norm:
                    await conn.execute(
                        text(
                            "INSERT INTO quest_tags(quest_id, slug) VALUES (cast(:id as uuid), :slug) ON CONFLICT DO NOTHING"
                        ),
                        {"id": str(quest_id), "slug": s},
                    )
            got = await self._araw_get(str(quest_id))
            if got is None:

                raise RuntimeError("database_row_missing")
            return got

        return run_sync(_run())

    def update(
        self,
        quest_id: str,
        *,
        title: str | None,
        description: str | None,
        is_public: bool | None,
    ) -> QuestDTO:

        async def _run() -> QuestDTO:
            sets = []
            params: dict[str, object] = {"id": str(quest_id)}
            if title is not None:
                sets.append("title = :title")
                params["title"] = title
            if description is not None:
                sets.append("description = :description")
                params["description"] = description
            if is_public is not None:
                sets.append("is_public = :pub")
                params["pub"] = bool(is_public)
            if sets:
                sql = text(
                    "UPDATE quests SET "
                    + ", ".join(sets)
                    + ", updated_at = now() WHERE id = cast(:id as uuid)"
                )
                async with self._engine.begin() as conn:
                    await conn.execute(sql, params)
            got = await self._araw_get(str(quest_id))
            if not got:
                raise ValueError("quest not found")
            return got

        return run_sync(_run())

    # --- internal async helpers ---
    async def _araw_get(self, quest_id: str) -> QuestDTO | None:
        sql = text(
            "SELECT id::text AS id, author_id::text AS author_id, slug, title, description, is_public FROM quests WHERE id = cast(:id as uuid)"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": str(quest_id)})).mappings().first()
        if not r:
            return None
        tags = await self._aload_tags([str(quest_id)])
        return QuestDTO(
            id=str(r["id"]),
            author_id=str(r["author_id"]),
            slug=str(r["slug"]),
            title=str(r["title"]),
            description=r["description"],
            tags=tags.get(str(quest_id), []),
            is_public=bool(r["is_public"]),
        )


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "quests repo: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("quests repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "quests repo: using memory backend (%s)", reason)


def create_repo(settings) -> Repo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return MemoryQuestsRepo()
    try:
        return SQLQuestsRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return MemoryQuestsRepo()


__all__ = [
    "SQLQuestsRepo",
    "create_repo",
]
