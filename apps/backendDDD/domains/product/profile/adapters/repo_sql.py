from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backendDDD.domains.product.profile.application.ports import Repo
from apps.backendDDD.domains.product.profile.domain.entities import Profile


class SQLProfileRepo(Repo):
    """Profile repo backed by users table.

    Reads/writes minimal subset: id, username, bio.
    """

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    def get(self, id: str) -> Profile | None:  # noqa: A002 - port name
        import asyncio

        async def _run() -> Profile | None:
            sql = text(
                "SELECT id::text AS id, username::text AS username, bio FROM users WHERE id = :id"
            )
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, {"id": id})).mappings().first()
                if not r or r.get("username") is None:
                    return None
                return Profile(
                    id=str(r["id"]), username=str(r["username"]), bio=r.get("bio")
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def upsert(self, p: Profile) -> Profile:
        import asyncio

        async def _run() -> Profile:
            sql = text(
                """
                INSERT INTO users(id, username, bio)
                VALUES (cast(:id as uuid), :username, :bio)
                ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, bio = EXCLUDED.bio
                RETURNING id::text AS id, username::text AS username, bio
                """
            )
            async with self._engine.begin() as conn:
                r = (
                    (
                        await conn.execute(
                            sql, {"id": p.id, "username": p.username, "bio": p.bio}
                        )
                    )
                    .mappings()
                    .first()
                )
                assert r is not None
                return Profile(
                    id=str(r["id"]), username=str(r["username"]), bio=r.get("bio")
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]


__all__ = ["SQLProfileRepo"]
