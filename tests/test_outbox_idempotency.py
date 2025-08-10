import pytest
from sqlalchemy import select

from app.models.idempotency import IdempotencyKey
from app.models.outbox import OutboxEvent, OutboxStatus
from app.services.outbox import emit


@pytest.mark.asyncio
async def test_idempotency_key_persistence(db_session):
    key = IdempotencyKey(
        key="abc",
        fingerprint="fp",
        status=200,
        response_sha256="deadbeef",
        payload_bytes=10,
    )
    db_session.add(key)
    await db_session.commit()

    result = await db_session.get(IdempotencyKey, "abc")
    assert result is not None
    assert result.fingerprint == "fp"
    assert result.status == 200


@pytest.mark.asyncio
async def test_outbox_emit_creates_event(db_session):
    event = await emit(db_session, "test.topic", {"hello": "world"}, dedup_key="k1")
    await db_session.commit()

    stmt = select(OutboxEvent).where(OutboxEvent.id == event.id)
    res = await db_session.execute(stmt)
    stored = res.scalar_one()
    assert stored.topic == "test.topic"
    assert stored.status == OutboxStatus.NEW
    assert stored.dedup_key == "k1"
