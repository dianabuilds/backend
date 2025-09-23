from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.worlds.application.ports import Repo
from domains.product.worlds.domain.entities import Character, WorldTemplate


class SQLWorldsRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        # If a DSN string is provided, create a short-lived engine per call.
        if isinstance(engine, str):
            self._engine: AsyncEngine | None = None
            self._dsn: str | None = str(engine)
        else:
            self._engine = engine
            self._dsn = None

    def _engine_for_call(self) -> tuple[AsyncEngine, bool]:
        if self._engine is not None:
            return self._engine, False
        if self._dsn is None:
            raise RuntimeError("SQLWorldsRepo requires an engine or DSN configuration")
        return create_async_engine(self._dsn), True

    # --- Worlds ---
    def list_worlds(self, workspace_id: str) -> list[WorldTemplate]:
        import asyncio

        async def _run() -> list[WorldTemplate]:
            sql = text(
                """
                SELECT id::text AS id, workspace_id::text AS workspace_id,
                       title, locale, description, meta,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                FROM worlds
                WHERE workspace_id = cast(:ws as uuid)
                ORDER BY created_at DESC
                """
            )
            eng = self._engine or create_async_engine(str(self._dsn))
            try:
                async with eng.begin() as conn:
                    rows = (await conn.execute(sql, {"ws": workspace_id})).mappings().all()
                    return [
                        WorldTemplate(
                            id=str(r["id"]),
                            workspace_id=str(r["workspace_id"]),
                            title=str(r["title"]),
                            locale=r["locale"],
                            description=r["description"],
                            meta=r["meta"] or {},
                            created_at=r["created_at"],
                            updated_at=r["updated_at"],
                            created_by_user_id=r.get("created_by_user_id"),
                            updated_by_user_id=r.get("updated_by_user_id"),
                        )
                        for r in rows
                    ]
            finally:
                if self._engine is None:
                    await eng.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def get_world(self, world_id: str, workspace_id: str) -> WorldTemplate | None:
        import asyncio

        async def _run() -> WorldTemplate | None:
            sql = text(
                """
                SELECT id::text AS id, workspace_id::text AS workspace_id,
                       title, locale, description, meta,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                FROM worlds
                WHERE id = cast(:id as uuid) AND workspace_id = cast(:ws as uuid)
                """
            )
            eng = self._engine or create_async_engine(str(self._dsn))
            try:
                async with eng.begin() as conn:
                    r = (
                        (await conn.execute(sql, {"id": world_id, "ws": workspace_id}))
                        .mappings()
                        .first()
                    )
                    if not r:
                        return None
                    return WorldTemplate(
                        id=str(r["id"]),
                        workspace_id=str(r["workspace_id"]),
                        title=str(r["title"]),
                        locale=r["locale"],
                        description=r["description"],
                        meta=r["meta"] or {},
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        created_by_user_id=r.get("created_by_user_id"),
                        updated_by_user_id=r.get("updated_by_user_id"),
                    )
            finally:
                if self._engine is None:
                    await eng.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def create_world(self, workspace_id: str, data: dict, actor_id: str) -> WorldTemplate:
        import asyncio

        async def _run() -> WorldTemplate:
            import json

            sql = text(
                """
                INSERT INTO worlds(
                    workspace_id, title, locale, description, meta,
                    created_by_user_id, updated_by_user_id
                )
                VALUES (cast(:ws as uuid), :title, :locale, :description, cast(:meta as jsonb), cast(:actor as uuid), cast(:actor as uuid))
                RETURNING id::text AS id, workspace_id::text AS workspace_id,
                          title, locale, description, meta,
                          created_at, updated_at,
                          created_by_user_id::text AS created_by_user_id,
                          updated_by_user_id::text AS updated_by_user_id
                """
            )
            params: dict[str, Any] = {
                "ws": workspace_id,
                "title": str(data.get("title") or "").strip(),
                "locale": data.get("locale"),
                "description": data.get("description"),
                "meta": json.dumps(data.get("meta") or {}),
                "actor": actor_id,
            }
            eng = self._engine or create_async_engine(str(self._dsn))
            try:
                async with eng.begin() as conn:
                    r = (await conn.execute(sql, params)).mappings().first()
                    assert r is not None
                    return WorldTemplate(
                        id=str(r["id"]),
                        workspace_id=str(r["workspace_id"]),
                        title=str(r["title"]),
                        locale=r["locale"],
                        description=r["description"],
                        meta=r["meta"] or {},
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        created_by_user_id=r.get("created_by_user_id"),
                        updated_by_user_id=r.get("updated_by_user_id"),
                    )
            finally:
                if self._engine is None:
                    await eng.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def update_world(
        self, world: WorldTemplate, data: dict, workspace_id: str, actor_id: str
    ) -> WorldTemplate:
        import asyncio

        async def _run() -> WorldTemplate:
            sets: list[str] = [
                "updated_at = now()",
                "updated_by_user_id = cast(:actor as uuid)",
            ]
            params: dict[str, Any] = {
                "id": world.id,
                "ws": workspace_id,
                "actor": actor_id,
            }
            if "title" in data and data["title"] is not None:
                sets.append("title = :title")
                params["title"] = str(data["title"]).strip()
            if "locale" in data:
                sets.append("locale = :locale")
                params["locale"] = data.get("locale")
            if "description" in data:
                sets.append("description = :description")
                params["description"] = data.get("description")
            if "meta" in data and data["meta"] is not None:
                import json

                sets.append("meta = cast(:meta as jsonb)")
                params["meta"] = json.dumps(dict(data["meta"]))  # shallow copy
            sql = text(
                "UPDATE worlds SET "
                + ", ".join(sets)
                + " WHERE id = cast(:id as uuid) AND workspace_id = cast(:ws as uuid)"
                + " RETURNING id::text AS id, workspace_id::text AS workspace_id, title, locale, description, meta, created_at, updated_at, created_by_user_id::text AS created_by_user_id, updated_by_user_id::text AS updated_by_user_id"
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    r = (await conn.execute(sql, params)).mappings().first()
                    if not r:
                        # World not matched (workspace mismatch?) — return original world
                        return world
                    return WorldTemplate(
                        id=str(r["id"]),
                        workspace_id=str(r["workspace_id"]),
                        title=str(r["title"]),
                        locale=r["locale"],
                        description=r["description"],
                        meta=r["meta"] or {},
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        created_by_user_id=r.get("created_by_user_id"),
                        updated_by_user_id=r.get("updated_by_user_id"),
                    )
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def delete_world(self, world: WorldTemplate, workspace_id: str) -> None:
        import asyncio

        async def _run() -> None:
            sql = text(
                "DELETE FROM worlds WHERE id = cast(:id as uuid) AND workspace_id = cast(:ws as uuid)"
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    await conn.execute(sql, {"id": world.id, "ws": workspace_id})
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.run_until_complete(_run())  # type: ignore[misc]

    # --- Characters ---
    def list_characters(self, world_id: str, workspace_id: str) -> list[Character]:
        import asyncio

        async def _run() -> list[Character]:
            # Ensure world belongs to workspace
            chk = text(
                "SELECT 1 FROM worlds WHERE id = cast(:id as uuid) AND workspace_id = cast(:ws as uuid)"
            )
            q = text(
                """
                SELECT id::text AS id, world_id::text AS world_id,
                       name, role, description, traits,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                FROM world_characters
                WHERE world_id = cast(:id as uuid)
                ORDER BY created_at DESC
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    ok = (await conn.execute(chk, {"id": world_id, "ws": workspace_id})).first()
                    if not ok:
                        return []
                    rows = (await conn.execute(q, {"id": world_id})).mappings().all()
                    return [
                        Character(
                            id=str(r["id"]),
                            world_id=str(r["world_id"]),
                            name=str(r["name"]),
                            role=r["role"],
                            description=r["description"],
                            traits=r["traits"] or {},
                            created_at=r["created_at"],
                            updated_at=r["updated_at"],
                            created_by_user_id=r.get("created_by_user_id"),
                            updated_by_user_id=r.get("updated_by_user_id"),
                        )
                        for r in rows
                    ]
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def get_character(self, char_id: str, workspace_id: str) -> Character | None:
        import asyncio

        async def _run() -> Character | None:
            sql = text(
                """
                SELECT c.id::text AS id, c.world_id::text AS world_id,
                       c.name, c.role, c.description, c.traits,
                       c.created_at, c.updated_at,
                       c.created_by_user_id::text AS created_by_user_id,
                       c.updated_by_user_id::text AS updated_by_user_id
                FROM world_characters c
                JOIN worlds w ON w.id = c.world_id
                WHERE c.id = cast(:cid as uuid) AND w.workspace_id = cast(:ws as uuid)
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    r = (
                        (await conn.execute(sql, {"cid": char_id, "ws": workspace_id}))
                        .mappings()
                        .first()
                    )
                    if not r:
                        return None
                    return Character(
                        id=str(r["id"]),
                        world_id=str(r["world_id"]),
                        name=str(r["name"]),
                        role=r["role"],
                        description=r["description"],
                        traits=r["traits"] or {},
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        created_by_user_id=r.get("created_by_user_id"),
                        updated_by_user_id=r.get("updated_by_user_id"),
                    )
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def create_character(
        self, world_id: str, workspace_id: str, data: dict, actor_id: str
    ) -> Character:
        import asyncio

        async def _run() -> Character:
            import json

            # Ensure world belongs to workspace
            chk = text(
                "SELECT 1 FROM worlds WHERE id = cast(:id as uuid) AND workspace_id = cast(:ws as uuid)"
            )
            ins = text(
                """
                INSERT INTO world_characters(
                    world_id, name, role, description, traits,
                    created_by_user_id, updated_by_user_id
                ) VALUES (cast(:wid as uuid), :name, :role, :description, cast(:traits as jsonb), cast(:actor as uuid), cast(:actor as uuid))
                RETURNING id::text AS id, world_id::text AS world_id,
                          name, role, description, traits,
                          created_at, updated_at,
                          created_by_user_id::text AS created_by_user_id,
                          updated_by_user_id::text AS updated_by_user_id
                """
            )
            params: dict[str, Any] = {
                "id": world_id,
                "ws": workspace_id,
                "wid": world_id,
                "name": str(data.get("name") or "").strip(),
                "role": data.get("role"),
                "description": data.get("description"),
                "traits": json.dumps(data.get("traits") or {}),
                "actor": actor_id,
            }
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    ok = (await conn.execute(chk, {"id": world_id, "ws": workspace_id})).first()
                    if not ok:
                        raise ValueError("world not found")
                    r = (await conn.execute(ins, params)).mappings().first()
                    assert r is not None
                    return Character(
                        id=str(r["id"]),
                        world_id=str(r["world_id"]),
                        name=str(r["name"]),
                        role=r["role"],
                        description=r["description"],
                        traits=r["traits"] or {},
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        created_by_user_id=r.get("created_by_user_id"),
                        updated_by_user_id=r.get("updated_by_user_id"),
                    )
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def update_character(
        self, ch: Character, data: dict, workspace_id: str, actor_id: str
    ) -> Character:
        import asyncio

        async def _run() -> Character:
            sets: list[str] = [
                "updated_at = now()",
                "updated_by_user_id = cast(:actor as uuid)",
            ]
            params: dict[str, Any] = {
                "id": ch.id,
                "ws": workspace_id,
                "actor": actor_id,
            }
            if "name" in data and data["name"] is not None:
                sets.append("name = :name")
                params["name"] = str(data["name"]).strip()
            if "role" in data:
                sets.append("role = :role")
                params["role"] = data.get("role")
            if "description" in data:
                sets.append("description = :description")
                params["description"] = data.get("description")
            if "traits" in data and data["traits"] is not None:
                import json

                sets.append("traits = cast(:traits as jsonb)")
                params["traits"] = json.dumps(dict(data["traits"]))  # shallow copy
            sql = text(
                """
                UPDATE world_characters AS c
                SET """
                + ", ".join(sets)
                + " FROM worlds w"
                + " WHERE c.id = cast(:id as uuid) AND w.id = c.world_id AND w.workspace_id = cast(:ws as uuid)"
                + " RETURNING c.id::text AS id, c.world_id::text AS world_id, c.name, c.role, c.description, c.traits, c.created_at, c.updated_at, c.created_by_user_id::text AS created_by_user_id, c.updated_by_user_id::text AS updated_by_user_id"
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    r = (await conn.execute(sql, params)).mappings().first()
                    if not r:
                        return ch
                    return Character(
                        id=str(r["id"]),
                        world_id=str(r["world_id"]),
                        name=str(r["name"]),
                        role=r["role"],
                        description=r["description"],
                        traits=r["traits"] or {},
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        created_by_user_id=r.get("created_by_user_id"),
                        updated_by_user_id=r.get("updated_by_user_id"),
                    )
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def delete_character(self, ch: Character, workspace_id: str) -> None:
        import asyncio

        async def _run() -> None:
            sql = text(
                """
                DELETE FROM world_characters AS c
                USING worlds AS w
                WHERE c.id = cast(:id as uuid)
                  AND w.id = c.world_id
                  AND w.workspace_id = cast(:ws as uuid)
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    await conn.execute(sql, {"id": ch.id, "ws": workspace_id})
            finally:
                if dispose:
                    await engine.dispose()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.run_until_complete(_run())  # type: ignore[misc]


__all__ = ["SQLWorldsRepo"]
