import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models.payment import Payment
from app.models.user import User


def _make_token(amount: int) -> str:
    return jwt.encode(
        {"amount": amount},
        settings.payment.jwt_secret,
        algorithm=settings.jwt.algorithm,
    )


@pytest.mark.asyncio
async def test_payments_rbac(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    moderator_user: User,
):
    token_mod = create_access_token(moderator_user.id)
    resp = await client.get(
        "/admin/payments",
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200

    token_user = create_access_token(test_user.id)
    resp = await client.get(
        "/admin/payments",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reverify_changes_status(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    moderator_user: User,
):
    pay_token = _make_token(5)
    payment = Payment(
        user_id=admin_user.id,
        source="webhook",
        days=5,
        status="failed",
        payload={"payment_token": pay_token},
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    token_mod = create_access_token(moderator_user.id)
    resp = await client.post(
        f"/admin/payments/{payment.id}/reverify",
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 403

    token_admin = create_access_token(admin_user.id)
    resp = await client.post(
        f"/admin/payments/{payment.id}/reverify",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == 200
    await db_session.refresh(payment)
    assert payment.status == "confirmed"
