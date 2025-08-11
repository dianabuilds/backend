import pytest
from fastapi import HTTPException
from datetime import datetime
from uuid import uuid4
from sqlalchemy.future import select

from app.core.pagination import (
    CursorPayload,
    build_cursor_for_last_item,
    decode_cursor,
    encode_cursor,
    parse_page_query,
    apply_sorting,
    apply_pagination,
    fetch_page,
)
from app.models.user import User


@pytest.mark.asyncio
async def test_parse_page_query_validation():
    with pytest.raises(HTTPException):
        parse_page_query({"limit": "0"}, allowed_sort=["id"], default_sort="id")
    with pytest.raises(HTTPException):
        parse_page_query({"limit": "10", "sort": "foo"}, allowed_sort=["id"], default_sort="id")
    with pytest.raises(HTTPException):
        parse_page_query({"limit": "10", "order": "foo"}, allowed_sort=["id"], default_sort="id")


def test_cursor_roundtrip():
    payload = CursorPayload(k=1, id=str(uuid4()), o="asc", s="id")
    cursor = encode_cursor(payload)
    assert decode_cursor(cursor) == payload
    with pytest.raises(HTTPException):
        decode_cursor("not-a-cursor")


@pytest.mark.asyncio
async def test_cursor_pagination(db_session):
    ts = datetime.utcnow()
    u1 = User(id=uuid4(), created_at=ts, email="a@example.com")
    u2 = User(id=uuid4(), created_at=ts, email="b@example.com")
    db_session.add_all([u1, u2])
    await db_session.commit()

    pq = parse_page_query({"limit": "1"}, allowed_sort=["created_at", "id"], default_sort="created_at")
    stmt = select(User)
    stmt = apply_sorting(stmt, model=User, sort_field=pq.sort, order=pq.order)
    stmt = apply_pagination(stmt, model=User, cursor=None, sort_field=pq.sort, order=pq.order)
    items, has_next = await fetch_page(stmt, session=db_session, limit=pq.limit)
    assert has_next is True
    cursor = build_cursor_for_last_item(items[-1], pq.sort, pq.order)
    payload = decode_cursor(cursor)
    stmt2 = select(User)
    stmt2 = apply_sorting(stmt2, model=User, sort_field=pq.sort, order=pq.order)
    stmt2 = apply_pagination(stmt2, model=User, cursor=payload, sort_field=pq.sort, order=pq.order)
    items2, has_next2 = await fetch_page(stmt2, session=db_session, limit=pq.limit)
    assert len(items2) == 1
    assert items2[0].id != items[0].id
    assert has_next2 is False
