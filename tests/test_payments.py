import jwt
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token
from app.domains.quests.infrastructure.models.quest_models import Quest, QuestPurchase
from app.domains.users.infrastructure.models.user import User


def _make_token(amount: int) -> str:
    return jwt.encode({"amount": amount}, settings.payment.jwt_secret, algorithm=settings.jwt.algorithm)


@pytest.mark.asyncio
async def test_buy_paid_and_free_quests(client: AsyncClient, db_session: AsyncSession, test_user: User):
    paid = Quest(title="Paid", author_id=test_user.id, price=10, is_draft=False)
    free = Quest(title="Free", author_id=test_user.id, price=0, is_draft=False)
    db_session.add_all([paid, free])
    await db_session.commit()
    await db_session.refresh(paid)
    await db_session.refresh(free)

    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Free quest
    resp = await client.post(f"/quests/{free.id}/buy", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "free"

    # Paid quest requires valid payment token
    resp = await client.post(f"/quests/{paid.id}/buy", json={"payment_token": "bad"}, headers=headers)
    assert resp.status_code == 400

    pay_token = _make_token(10)
    resp = await client.post(
        f"/quests/{paid.id}/buy", json={"payment_token": pay_token}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Already purchased
    resp = await client.post(
        f"/quests/{paid.id}/buy", json={"payment_token": pay_token}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "already"

    result = await db_session.execute(
        select(QuestPurchase).where(QuestPurchase.quest_id == paid.id)
    )
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_buy_premium_subscription(client: AsyncClient, db_session: AsyncSession, test_user: User):
    token = create_access_token(test_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    invalid = await client.post(
        "/payments/premium", json={"payment_token": "bad", "days": 10}, headers=headers
    )
    assert invalid.status_code == 400

    pay_token = _make_token(10)
    resp = await client.post(
        "/payments/premium", json={"payment_token": pay_token, "days": 10}, headers=headers
    )
    assert resp.status_code == 200
    await db_session.refresh(test_user)
    assert test_user.is_premium is True
    assert test_user.premium_until and test_user.premium_until > datetime.utcnow()
