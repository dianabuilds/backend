import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domains.users.infrastructure.models.user import User


@pytest.mark.asyncio
async def test_admin_crud_subscription_plans(
    client: AsyncClient, db_session: AsyncSession, admin_user: User
) -> None:
    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Initially empty
    resp = await client.get("/admin/premium/plans", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    payload = {
        "slug": "gold",
        "title": "Gold",
        "description": "desc",
        "price_cents": 1000,
        "currency": "USD",
        "is_active": True,
        "order": 1,
        "monthly_limits": {"stories": 10},
        "features": {},
    }

    resp = await client.post("/admin/premium/plans", json=payload, headers=headers)
    assert resp.status_code == 200
    plan = resp.json()
    assert plan["slug"] == "gold"
    plan_id = plan["id"]

    # Update
    payload["title"] = "Gold+"
    resp = await client.put(
        f"/admin/premium/plans/{plan_id}", json=payload, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Gold+"

    # Delete
    resp = await client.delete(f"/admin/premium/plans/{plan_id}", headers=headers)
    assert resp.status_code == 200

    resp = await client.get("/admin/premium/plans", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []
