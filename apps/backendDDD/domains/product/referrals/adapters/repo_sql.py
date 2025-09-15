from __future__ import annotations

import asyncio
import uuid as _uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backendDDD.domains.product.referrals.application.ports import Repo
from apps.backendDDD.domains.product.referrals.domain.entities import (
    ReferralCode,
    ReferralEvent,
)


class SQLReferralsRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def get_personal_code(self, owner_user_id: str) -> ReferralCode | None:
        sql = text(
            "SELECT id::text AS id, owner_user_id::text AS owner_user_id, code, active, uses_count, created_at FROM product_referral_codes WHERE owner_user_id = cast(:uid as uuid)"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"uid": owner_user_id})).mappings().first()
        if not r:
            return None
        return ReferralCode(
            id=str(r["id"]),
            owner_user_id=str(r["owner_user_id"]),
            code=str(r["code"]),
            active=bool(r["active"]),
            uses_count=int(r["uses_count"]),
            created_at=r["created_at"],
        )

    async def create_personal_code(self, owner_user_id: str, code: str) -> ReferralCode:
        sql = text(
            """
            INSERT INTO product_referral_codes(owner_user_id, code)
            VALUES (cast(:uid as uuid), :code)
            RETURNING id::text AS id, owner_user_id::text AS owner_user_id, code, active, uses_count, created_at
            """
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"uid": owner_user_id, "code": code})).mappings().first()
            assert r is not None
            return ReferralCode(
                id=str(r["id"]),
                owner_user_id=str(r["owner_user_id"]),
                code=str(r["code"]),
                active=bool(r["active"]),
                uses_count=int(r["uses_count"]),
                created_at=r["created_at"],
            )

    async def find_code(self, code: str) -> ReferralCode | None:
        sql = text(
            "SELECT id::text AS id, owner_user_id::text AS owner_user_id, code, active, uses_count, created_at FROM product_referral_codes WHERE code = :code AND active"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"code": code})).mappings().first()
        if not r:
            return None
        return ReferralCode(
            id=str(r["id"]),
            owner_user_id=str(r["owner_user_id"]),
            code=str(r["code"]),
            active=bool(r["active"]),
            uses_count=int(r["uses_count"]),
            created_at=r["created_at"],
        )

    async def record_signup(
        self, *, code: ReferralCode, referee_user_id: str, meta: dict | None = None
    ) -> ReferralEvent | None:
        # Prevent duplicate signup by the same referee
        dup = text(
            "SELECT 1 FROM product_referral_events WHERE referee_user_id = cast(:rid as uuid) AND event_type = 'signup'"
        )
        ins = text(
            """
            INSERT INTO product_referral_events(code_id, code, referrer_user_id, referee_user_id, event_type, meta)
            VALUES (cast(:cid as uuid), :code, cast(:ref as uuid), cast(:rid as uuid), 'signup', :meta)
            RETURNING id::text AS id, code_id::text AS code_id, code, referrer_user_id::text AS referrer_user_id,
                      referee_user_id::text AS referee_user_id, event_type, occurred_at, meta
            """
        )
        async with self._engine.begin() as conn:
            exists = (await conn.execute(dup, {"rid": referee_user_id})).first()
            if exists:
                return None
            r = (
                await conn.execute(
                    ins,
                    {
                        "cid": code.id,
                        "code": code.code,
                        "ref": code.owner_user_id,
                        "rid": referee_user_id,
                        "meta": dict(meta or {}),
                    },
                )
            ).mappings().first()
        assert r is not None
        # Increment counter separately
        await self._increment_uses(code.id)
        return ReferralEvent(
            id=str(r["id"]),
            code_id=str(r["code_id"]) if r["code_id"] else None,
            code=str(r["code"]) if r["code"] else None,
            referrer_user_id=str(r["referrer_user_id"]) if r["referrer_user_id"] else None,
            referee_user_id=str(r["referee_user_id"]),
            event_type=str(r["event_type"]),
            occurred_at=r["occurred_at"],
            meta=dict(r["meta"] or {}),
        )

    async def _increment_uses(self, code_id: str) -> None:
        sql = text(
            "UPDATE product_referral_codes SET uses_count = uses_count + 1 WHERE id = cast(:id as uuid)"
        )
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": code_id})

    async def count_signups(self, referrer_user_id: str) -> int:
        sql = text(
            "SELECT count(*)::int AS c FROM product_referral_events WHERE referrer_user_id = cast(:uid as uuid) AND event_type = 'signup'"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"uid": referrer_user_id})).mappings().first()
        return int(r.get("c") or 0)  # type: ignore[return-value]

    async def list_codes(
        self, *, owner_user_id: str | None, active: bool | None, limit: int, offset: int
    ) -> list[ReferralCode]:
        where = []
        params: dict[str, Any] = {"limit": int(limit), "offset": int(offset)}
        if owner_user_id is not None:
            where.append("owner_user_id = cast(:uid as uuid)")
            params["uid"] = owner_user_id
        if active is not None:
            where.append("active = :active")
            params["active"] = bool(active)
        sql = text(
            "SELECT id::text AS id, owner_user_id::text AS owner_user_id, code, active, uses_count, created_at FROM product_referral_codes"
            + (" WHERE " + " AND ".join(where) if where else "")
            + " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, params)).mappings().all()
        return [
            ReferralCode(
                id=str(r["id"]),
                owner_user_id=str(r["owner_user_id"]),
                code=str(r["code"]),
                active=bool(r["active"]),
                uses_count=int(r["uses_count"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    async def list_events(
        self, *, referrer_user_id: str | None, limit: int, offset: int
    ) -> list[ReferralEvent]:
        where = ["event_type = 'signup'"]
        params: dict[str, Any] = {"limit": int(limit), "offset": int(offset)}
        if referrer_user_id is not None:
            where.append("referrer_user_id = cast(:uid as uuid)")
            params["uid"] = referrer_user_id
        sql = text(
            "SELECT id::text AS id, code_id::text AS code_id, code, referrer_user_id::text AS referrer_user_id, referee_user_id::text AS referee_user_id, event_type, occurred_at, meta FROM product_referral_events"
            + (" WHERE " + " AND ".join(where) if where else "")
            + " ORDER BY occurred_at DESC LIMIT :limit OFFSET :offset"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, params)).mappings().all()
        return [
            ReferralEvent(
                id=str(r["id"]),
                code_id=str(r["code_id"]) if r["code_id"] else None,
                code=str(r["code"]) if r["code"] else None,
                referrer_user_id=str(r["referrer_user_id"]) if r["referrer_user_id"] else None,
                referee_user_id=str(r["referee_user_id"]),
                event_type=str(r["event_type"]),
                occurred_at=r["occurred_at"],
                meta=dict(r["meta"] or {}),
            )
            for r in rows
        ]

    async def generate_unique_code(self, prefix: str = "ref-") -> str:
        for _ in range(20):
            c = (prefix + _uuid.uuid4().hex[:12]).lower()
            sql = text("SELECT 1 FROM product_referral_codes WHERE code = :code")
            async with self._engine.begin() as conn:
                exists = (await conn.execute(sql, {"code": c})).first()
                if not exists:
                    return c
        return (prefix + _uuid.uuid4().hex[:16]).lower()

    async def set_active(self, owner_user_id: str, active: bool) -> ReferralCode | None:
        # Upsert on activation if missing
        if active:
            code = await self.get_personal_code(owner_user_id)
            if code is None:
                gen = await self.generate_unique_code()
                return await self.create_personal_code(owner_user_id, gen)
        sql = text(
            "UPDATE product_referral_codes SET active = :active WHERE owner_user_id = cast(:uid as uuid) RETURNING id::text AS id, owner_user_id::text AS owner_user_id, code, active, uses_count, created_at"
        )
        async with self._engine.begin() as conn:
            r = (
                await conn.execute(sql, {"active": bool(active), "uid": owner_user_id})
            ).mappings().first()
        if not r:
            return None
        return ReferralCode(
            id=str(r["id"]),
            owner_user_id=str(r["owner_user_id"]),
            code=str(r["code"]),
            active=bool(r["active"]),
            uses_count=int(r["uses_count"]),
            created_at=r["created_at"],
        )


__all__ = ["SQLReferralsRepo"]

