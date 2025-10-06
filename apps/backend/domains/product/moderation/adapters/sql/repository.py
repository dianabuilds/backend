from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.moderation.application.ports import Repo
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.repository import MemoryRepo

logger = logging.getLogger(__name__)


def _norm(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    return [str(v).strip().lower() for v in values if str(v).strip()]


def _ensure_dict(value: object) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return {}
    if isinstance(value, str):
        try:
            return dict(json.loads(value))
        except (json.JSONDecodeError, TypeError, ValueError):
            return {}
    return {}


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone().isoformat()
    return str(value)


_ALLOWED_MUTABLE_FIELDS = {
    "title",
    "description",
    "type",
    "queue",
    "priority",
    "severity",
    "subject_id",
    "subject_type",
    "subject_label",
    "assignee_id",
    "tags",
    "metadata",
}


class SQLModerationRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            get_async_engine("product-moderation", url=engine)
            if isinstance(engine, str)
            else engine
        )

    async def list_cases(
        self,
        *,
        page: int,
        size: int,
        statuses: Sequence[str] | None = None,
        types: Sequence[str] | None = None,
        queues: Sequence[str] | None = None,
        assignees: Sequence[str] | None = None,
        query: str | None = None,
    ) -> dict:
        page = max(1, int(page or 1))
        size = max(1, min(int(size or 20), 200))
        offs = (page - 1) * size

        conditions: list[str] = []
        params: dict[str, object] = {}

        sts = _norm(statuses)
        if sts:
            conditions.append("lower(status) = ANY(:st)")
            params["st"] = sts

        tps = _norm(types)
        if tps:
            conditions.append("lower(data->>'type') = ANY(:types)")
            params["types"] = tps

        qs = _norm(queues)
        if qs:
            conditions.append("lower(data->>'queue') = ANY(:queues)")
            params["queues"] = qs

        ass = [str(a).strip() for a in assignees or [] if str(a).strip()]
        if ass:
            conditions.append("data->>'assignee_id' = ANY(:assignees)")
            params["assignees"] = ass

        needle = (query or "").strip()
        if needle:
            params["q"] = f"%{needle}%"
            conditions.append(
                "("
                "data->>'title' ILIKE :q OR "
                "data->>'description' ILIKE :q OR "
                "data->>'subject_id' ILIKE :q OR "
                "data->>'subject_label' ILIKE :q OR "
                "id::text ILIKE :q"
                ")"
            )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        base_from = "FROM moderation_cases"
        if where_clause:
            base_from = f"{base_from} {where_clause}"

        q_items = text(
            "SELECT id::text AS id, status, data, created_at, updated_at, "
            "created_by_user_id::text AS created_by_user_id "
            f"{base_from} "
            "ORDER BY created_at DESC "
            "LIMIT :lim OFFSET :off"
        )
        q_total = text(f"SELECT count(*)::int AS c {base_from}")

        async with self._engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        q_items,
                        {**params, "lim": size, "off": offs},
                    )
                )
                .mappings()
                .all()
            )
            total_row = (await conn.execute(q_total, params)).mappings().first()
            total = int(total_row.get("c") if total_row else 0)

        items: list[dict] = []
        for r in rows:
            data = _ensure_dict(r.get("data"))
            data.setdefault("type", str(data.get("type", "general")))
            data.pop("history", None)
            item = {
                **data,
                "id": str(r["id"]),
                "status": str(r["status"]),
                "created_at": _to_iso(r.get("created_at")),
                "updated_at": _to_iso(r.get("updated_at")),
            }
            created_by = r.get("created_by_user_id")
            if created_by:
                item["created_by_user_id"] = created_by
            items.append(item)

        return {"items": items, "total": total, "page": page, "size": size}

    async def create_case(self, payload: dict, *, created_by: str | None = None) -> str:
        data = dict(payload)
        status = str(data.pop("status", payload.get("status", "open")) or "open")
        history = [
            {
                "id": str(uuid.uuid4()),
                "type": "created",
                "title": "Case created",
                "actor": created_by,
                "created_at": _to_iso(datetime.now(UTC)),
            }
        ]
        data["history"] = history
        sql = text(
            "INSERT INTO moderation_cases(data, status, created_by_user_id) "
            "VALUES (cast(:d as jsonb), :st, :created_by) RETURNING id::text AS id"
        )
        json_payload = json.dumps(data)
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        sql,
                        {"d": json_payload, "st": status, "created_by": created_by},
                    )
                )
                .mappings()
                .first()
            )
            assert row is not None
            return str(row["id"])

    async def add_note(
        self, case_id: str, note: dict, *, author_id: str | None
    ) -> dict | None:
        chk = text("SELECT 1 FROM moderation_cases WHERE id = cast(:id as uuid)")
        ins = text(
            "INSERT INTO moderation_notes(case_id, author_id, data) "
            "VALUES (cast(:cid as uuid), :aid, cast(:d as jsonb)) "
            "RETURNING id::text AS id, created_at, data"
        )
        touch = text(
            "UPDATE moderation_cases SET updated_at = now() "
            "WHERE id = cast(:cid as uuid)"
        )
        payload_json = json.dumps(dict(note))
        async with self._engine.begin() as conn:
            ok = (await conn.execute(chk, {"id": case_id})).first()
            if not ok:
                return None
            row = (
                (
                    await conn.execute(
                        ins,
                        {"cid": case_id, "aid": author_id, "d": payload_json},
                    )
                )
                .mappings()
                .first()
            )
            await conn.execute(touch, {"cid": case_id})
        if not row:
            return None
        data = _ensure_dict(row.get("data"))
        data.update(
            {
                "id": str(row["id"]),
                "author_id": author_id,
                "created_at": _to_iso(row.get("created_at")),
            }
        )
        return data

    async def get_case(self, case_id: str) -> dict | None:
        sql = text(
            "SELECT id::text AS id, status, data, created_at, updated_at, "
            "created_by_user_id::text AS created_by_user_id "
            "FROM moderation_cases WHERE id = cast(:id as uuid)"
        )
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"id": case_id})).mappings().first()
        if not row:
            return None
        data = _ensure_dict(row.get("data"))
        data.setdefault("type", str(data.get("type", "general")))
        data.pop("history", None)
        result = {
            **data,
            "id": str(row["id"]),
            "status": str(row["status"]),
            "created_at": _to_iso(row.get("created_at")),
            "updated_at": _to_iso(row.get("updated_at")),
        }
        created_by = row.get("created_by_user_id")
        if created_by:
            result["created_by_user_id"] = created_by
        return result

    async def list_notes(self, case_id: str) -> list[dict]:
        sql = text(
            "SELECT id::text AS id, author_id::text AS author_id, data, created_at "
            "FROM moderation_notes WHERE case_id = cast(:id as uuid) "
            "ORDER BY created_at DESC"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, {"id": case_id})).mappings().all()
        notes: list[dict] = []
        for row in rows:
            data = _ensure_dict(row.get("data"))
            data.update(
                {
                    "id": str(row["id"]),
                    "author_id": row.get("author_id"),
                    "created_at": _to_iso(row.get("created_at")),
                }
            )
            notes.append(data)
        return notes

    async def list_events(self, case_id: str) -> list[dict]:
        sql = text("SELECT data FROM moderation_cases WHERE id = cast(:id as uuid)")
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"id": case_id})).mappings().first()
        if not row:
            return []
        data = _ensure_dict(row.get("data"))
        history = data.get("history")
        if not isinstance(history, list):
            return []
        result: list[dict] = []
        for entry in history:
            if isinstance(entry, dict):
                result.append(dict(entry))
        result.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        return result

    async def update_case(
        self, case_id: str, payload: dict, *, actor_id: str | None
    ) -> dict | None:
        select_sql = text(
            "SELECT data, status FROM moderation_cases WHERE id = cast(:id as uuid)"
        )
        async with self._engine.begin() as conn:
            row = (await conn.execute(select_sql, {"id": case_id})).mappings().first()
            if not row:
                return None
            current_data = _ensure_dict(row.get("data"))
            current_status = str(row.get("status"))
            history = list(current_data.get("history", []))
            new_data = dict(current_data)
            new_status = current_status
            now = datetime.now(UTC)
            for key, value in payload.items():
                if key not in _ALLOWED_MUTABLE_FIELDS:
                    continue
                previous = new_data.get(key)
                if previous != value:
                    new_data[key] = value
                    history.append(
                        {
                            "id": str(uuid.uuid4()),
                            "type": f"{key}_changed",
                            "field": key,
                            "from": previous,
                            "to": value,
                            "actor": actor_id,
                            "title": f"{key.replace('_', ' ').title()} updated",
                            "description": f"{previous or '-'} → {value or '-'}",
                            "created_at": _to_iso(now),
                        }
                    )
            if "status" in payload and payload["status"] is not None:
                new_status = str(payload["status"])
            new_data["history"] = history
            update_sql = text(
                "UPDATE moderation_cases "
                "SET data = cast(:d as jsonb), status = :st, updated_at = now() "
                "WHERE id = cast(:id as uuid)"
            )
            await conn.execute(
                update_sql,
                {
                    "id": case_id,
                    "d": json.dumps(new_data),
                    "st": new_status,
                },
            )
        return await self.get_case(case_id)


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "product moderation repo: falling back to memory due to SQL error: %s",
            error,
        )
        return
    if not reason:
        logger.debug("product moderation repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "product moderation repo: using memory backend (%s)", reason)


def create_repo(settings) -> Repo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return MemoryRepo()
    try:
        return SQLModerationRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return MemoryRepo()


__all__ = [
    "SQLModerationRepo",
    "create_repo",
]
