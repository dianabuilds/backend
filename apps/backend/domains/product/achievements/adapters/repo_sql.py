from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.achievements.application.ports import Repo
from domains.product.achievements.domain.entities import (
    Achievement,
    UserAchievement,
)


class SQLRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    # --- User views ---
    def list_for_user(self, user_id: str) -> Iterable[tuple[Achievement, UserAchievement | None]]:
        async def _run() -> list[tuple[Achievement, UserAchievement | None]]:
            sql = text(
                """
                SELECT a.id::text AS id, a.code, a.title, a.description, a.icon, a.visible, a.condition,
                       a.created_by_user_id::text AS created_by_user_id,
                       a.updated_by_user_id::text AS updated_by_user_id,
                       a.created_at, a.updated_at,
                       g.unlocked_at
                FROM achievements AS a
                LEFT JOIN product_achievement_grants AS g
                  ON g.achievement_id = a.id AND g.user_id = cast(:uid as uuid)
                ORDER BY a.title ASC
                """
            )
            async with self._engine.begin() as conn:
                rows = (await conn.execute(sql, {"uid": user_id})).mappings().all()
            out: list[tuple[Achievement, UserAchievement | None]] = []
            for r in rows:
                a = Achievement(
                    id=str(r["id"]),
                    code=str(r["code"]),
                    title=str(r["title"]),
                    description=r["description"],
                    icon=r["icon"],
                    visible=bool(r["visible"]),
                    condition=dict(r["condition"] or {}),
                    created_by_user_id=r.get("created_by_user_id"),
                    updated_by_user_id=r.get("updated_by_user_id"),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                ua = None
                if r["unlocked_at"] is not None:
                    ua = UserAchievement(
                        user_id=str(user_id),
                        achievement_id=a.id,
                        unlocked_at=r["unlocked_at"],
                    )
                out.append((a, ua))
            return out

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def grant(self, user_id: str, achievement_id: str) -> bool:
        async def _run() -> bool:
            ins = text(
                """
                INSERT INTO product_achievement_grants(user_id, achievement_id)
                VALUES (cast(:uid as uuid), cast(:aid as uuid))
                ON CONFLICT DO NOTHING
                """
            )
            async with self._engine.begin() as conn:
                res = await conn.execute(ins, {"uid": user_id, "aid": achievement_id})
                try:
                    rc = res.rowcount  # type: ignore[attr-defined]
                except Exception:
                    rc = None
            return bool(rc and rc > 0)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def revoke(self, user_id: str, achievement_id: str) -> bool:
        async def _run() -> bool:
            sql = text(
                "DELETE FROM product_achievement_grants WHERE user_id = cast(:uid as uuid) AND achievement_id = cast(:aid as uuid)"
            )
            async with self._engine.begin() as conn:
                res = await conn.execute(sql, {"uid": user_id, "aid": achievement_id})
                try:
                    rc = res.rowcount  # type: ignore[attr-defined]
                except Exception:
                    rc = None
            return bool(rc and rc > 0)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    # --- Admin ---
    def list_all(self) -> list[Achievement]:
        async def _run() -> list[Achievement]:
            sql = text(
                """
                SELECT id::text AS id, code, title, description, icon, visible, condition,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id,
                       created_at, updated_at
                FROM achievements
                ORDER BY title ASC
                """
            )
            async with self._engine.begin() as conn:
                rows = (await conn.execute(sql)).mappings().all()
            return [
                Achievement(
                    id=str(r["id"]),
                    code=str(r["code"]),
                    title=str(r["title"]),
                    description=r["description"],
                    icon=r["icon"],
                    visible=bool(r["visible"]),
                    condition=dict(r["condition"] or {}),
                    created_by_user_id=r.get("created_by_user_id"),
                    updated_by_user_id=r.get("updated_by_user_id"),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def get(self, achievement_id: str) -> Achievement | None:
        async def _run() -> Achievement | None:
            sql = text(
                """
                SELECT id::text AS id, code, title, description, icon, visible, condition,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id,
                       created_at, updated_at
                FROM achievements WHERE id = cast(:id as uuid)
                """
            )
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, {"id": achievement_id})).mappings().first()
            if not r:
                return None
            return Achievement(
                id=str(r["id"]),
                code=str(r["code"]),
                title=str(r["title"]),
                description=r["description"],
                icon=r["icon"],
                visible=bool(r["visible"]),
                condition=dict(r["condition"] or {}),
                created_by_user_id=r.get("created_by_user_id"),
                updated_by_user_id=r.get("updated_by_user_id"),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def exists_code(self, code: str) -> bool:
        async def _run() -> bool:
            sql = text("SELECT 1 FROM achievements WHERE code = :code")
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, {"code": code})).first()
            return bool(r)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def create(self, data: dict) -> Achievement:
        async def _run() -> Achievement:
            sql = text(
                """
                INSERT INTO achievements(
                    code, title, description, icon, visible, condition,
                    created_by_user_id, updated_by_user_id
                ) VALUES (
                    :code, :title, :description, :icon, :visible, :condition,
                    cast(:cb as uuid), cast(:ub as uuid)
                )
                RETURNING id::text AS id, code, title, description, icon, visible, condition,
                          created_by_user_id::text AS created_by_user_id,
                          updated_by_user_id::text AS updated_by_user_id,
                          created_at, updated_at
                """
            )
            params: dict[str, Any] = {
                "code": str(data.get("code") or "").strip(),
                "title": str(data.get("title") or "").strip(),
                "description": data.get("description"),
                "icon": data.get("icon"),
                "visible": bool(data.get("visible", True)),
                "condition": dict(data.get("condition") or {}),
                "cb": data.get("created_by_user_id"),
                "ub": data.get("updated_by_user_id"),
            }
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, params)).mappings().first()
                assert r is not None
                return Achievement(
                    id=str(r["id"]),
                    code=str(r["code"]),
                    title=str(r["title"]),
                    description=r["description"],
                    icon=r["icon"],
                    visible=bool(r["visible"]),
                    condition=dict(r["condition"] or {}),
                    created_by_user_id=r.get("created_by_user_id"),
                    updated_by_user_id=r.get("updated_by_user_id"),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def update(self, achievement_id: str, data: dict) -> Achievement | None:
        async def _run() -> Achievement | None:
            # conflict check for code uniqueness when changed
            if "code" in data and data["code"] is not None:
                new_code = str(data["code"]).strip()
                chk = text(
                    "SELECT 1 FROM achievements WHERE code = :code AND id <> cast(:id as uuid)"
                )
                async with self._engine.begin() as conn:
                    conflict = (
                        await conn.execute(chk, {"code": new_code, "id": achievement_id})
                    ).first()
                if conflict:
                    return None
            sets = ["updated_at = now()"]
            params: dict[str, Any] = {"id": achievement_id}
            for field in (
                "code",
                "title",
                "description",
                "icon",
                "visible",
                "condition",
            ):
                if field in data:
                    sets.append(f"{field} = :{field}")
                    params[field] = data[field]
            if "updated_by_user_id" in data:
                sets.append("updated_by_user_id = cast(:ub as uuid)")
                params["ub"] = data["updated_by_user_id"]
            if len(sets) == 1:
                # nothing to update
                return self.get(achievement_id)
            sql = text(
                "UPDATE achievements SET "
                + ", ".join(sets)
                + " WHERE id = cast(:id as uuid)"
                + " RETURNING id::text AS id, code, title, description, icon, visible, condition,"
                + " created_by_user_id::text AS created_by_user_id, updated_by_user_id::text AS updated_by_user_id, created_at, updated_at"
            )
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, params)).mappings().first()
            if not r:
                return None
            return Achievement(
                id=str(r["id"]),
                code=str(r["code"]),
                title=str(r["title"]),
                description=r["description"],
                icon=r["icon"],
                visible=bool(r["visible"]),
                condition=dict(r["condition"] or {}),
                created_by_user_id=r.get("created_by_user_id"),
                updated_by_user_id=r.get("updated_by_user_id"),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def delete(self, achievement_id: str) -> bool:
        async def _run() -> bool:
            sql = text("DELETE FROM achievements WHERE id = cast(:id as uuid)")
            async with self._engine.begin() as conn:
                res = await conn.execute(sql, {"id": achievement_id})
                try:
                    rc = res.rowcount  # type: ignore[attr-defined]
                except Exception:
                    rc = None
            return bool(rc and rc > 0)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]


__all__ = ["SQLRepo"]
