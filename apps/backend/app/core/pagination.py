from __future__ import annotations

import base64
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.sql import Select


@dataclass
class PageQuery:
    limit: int
    cursor: str | None
    sort: str
    order: Literal["asc", "desc"]


@dataclass
class CursorPayload:
    k: Any
    id: str
    o: Literal["asc", "desc"]
    s: str


def parse_page_query(
    params: Mapping[str, str],
    *,
    allowed_sort: Sequence[str],
    default_sort: str,
) -> PageQuery:
    """Parse pagination-related query parameters.

    Unknown parameters are ignored. Validation errors raise HTTPException 400.
    """

    raw_limit = params.get("limit", "25")
    try:
        limit = int(raw_limit)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid limit") from err
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=400, detail="Invalid limit")

    order = params.get("order", "desc").lower()
    if order not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="Invalid order")

    sort = params.get("sort", default_sort)
    if sort not in allowed_sort:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    cursor = params.get("cursor")

    return PageQuery(limit=limit, cursor=cursor, sort=sort, order=order)  # type: ignore[arg-type]


def _b64encode(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def _b64decode(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode()


def encode_cursor(payload: CursorPayload) -> str:
    return _b64encode(json.dumps(payload.__dict__))


def decode_cursor(cursor: str) -> CursorPayload:
    try:
        raw = _b64decode(cursor)
        data = json.loads(raw)
        return CursorPayload(**data)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc


def build_cursor_for_last_item(item: Any, sort_field: str, order: str) -> str:
    value = getattr(item, sort_field)
    if isinstance(value, datetime):
        value = value.isoformat()
    payload = CursorPayload(k=value, id=str(item.id), o=order, s=sort_field)
    return encode_cursor(payload)


def apply_sorting(
    stmt: Select,
    *,
    model: Any,
    sort_field: str,
    order: str,
    tie_breaker: str = "id",
) -> Select:
    primary_col = getattr(model, sort_field)
    tie_col = getattr(model, tie_breaker)
    if order == "asc":
        stmt = stmt.order_by(primary_col.asc(), tie_col.asc())
    else:
        stmt = stmt.order_by(primary_col.desc(), tie_col.desc())
    return stmt


def apply_pagination(
    stmt: Select,
    *,
    model: Any,
    cursor: CursorPayload | None,
    sort_field: str,
    order: str,
    tie_breaker: str = "id",
) -> Select:
    if not cursor:
        return stmt
    primary_col = getattr(model, sort_field)
    tie_col = getattr(model, tie_breaker)
    key = cursor.k
    col_type = getattr(primary_col.type, "python_type", None)
    if col_type is datetime and isinstance(key, str):
        key = datetime.fromisoformat(key)
    last_id = UUID(cursor.id)
    if order == "desc":
        cond = or_(primary_col < key, and_(primary_col == key, tie_col < last_id))
    else:
        cond = or_(primary_col > key, and_(primary_col == key, tie_col > last_id))
    return stmt.where(cond)


async def fetch_page(
    stmt: Select,
    *,
    session,
    limit: int,
) -> tuple[Sequence[Any], bool]:
    """Execute statement with cursor pagination logic.

    The function fetches ``limit + 1`` rows to determine whether another page
    exists.  Only ``limit`` items are returned to the caller.
    """

    stmt = stmt.limit(limit + 1)
    result = await session.execute(stmt)
    items = result.scalars().all()
    has_next = len(items) > limit
    if has_next:
        items = items[:limit]
    return items, has_next


FilterHandler = Callable[[Select, Any], Select]
FilterSpec = Mapping[str, tuple[Callable[[str], Any], FilterHandler]]


def extract_filters(params: Mapping[str, str]) -> dict[str, str]:
    return {k[2:]: v for k, v in params.items() if k.startswith("f_")}


def apply_filters(
    stmt: Select, filters: Mapping[str, str], spec: FilterSpec
) -> tuple[Select, dict[str, Any]]:
    applied: dict[str, Any] = {}
    for key, raw in filters.items():
        if key not in spec:
            continue
        parser, handler = spec[key]
        try:
            value = parser(raw)
        except Exception as err:
            raise HTTPException(
                status_code=400, detail=f"Invalid filter: {key}"
            ) from err
        stmt = handler(stmt, value)
        applied[key] = value
    return stmt, applied


def scope_by_workspace(query: Select, workspace_id: UUID) -> Select:
    """Filter a SQLAlchemy query by workspace identifier if possible."""
    entity = query.column_descriptions[0]["entity"]
    if hasattr(entity, "workspace_id"):
        query = query.where(entity.workspace_id == workspace_id)
    return query
