from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from tests.integration.conftest import test_engine

from app.domains.ai.infrastructure.models.ai_settings import AISettings
from app.domains.ai.infrastructure.models.system_models import (
    AIDefaultModel,
    AIModelPrice,
    AISystemModel,
)


@pytest_asyncio.fixture()
async def ai_tables(db_session: AsyncSession) -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(AISettings.__table__.create, checkfirst=True)
        await conn.run_sync(AISystemModel.__table__.create, checkfirst=True)
        await conn.run_sync(AIModelPrice.__table__.create, checkfirst=True)
        await conn.run_sync(AIDefaultModel.__table__.create, checkfirst=True)
    yield
    for table in [
        AISettings.__table__,
        AISystemModel.__table__,
        AIModelPrice.__table__,
        AIDefaultModel.__table__,
    ]:
        await db_session.execute(text(f"DELETE FROM {table.name}"))
    await db_session.commit()


@pytest_asyncio.fixture()
async def admin_headers(
    db_session: AsyncSession, test_user, auth_headers
) -> dict[str, str]:
    await db_session.execute(
        text("UPDATE users SET role='admin' WHERE id=:id"), {"id": test_user.id}
    )
    await db_session.commit()
    return auth_headers


@pytest_asyncio.fixture()
async def client_with_domains(client: AsyncClient) -> AsyncClient:
    from app.domains.ai.api import routers as ai_routers

    client._transport.app.include_router(ai_routers.router)  # type: ignore[attr-defined]
    return client


@pytest.mark.asyncio
async def test_providers_crud(
    client_with_domains: AsyncClient, admin_headers: dict[str, str], ai_tables: None
) -> None:
    resp = await client_with_domains.get(
        "/admin/ai/system/providers", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []

    payload = {
        "code": "openai",
        "base_url": "http://api.example",
        "model": "gpt-4",
        "api_key": "secret",
    }
    resp = await client_with_domains.post(
        "/admin/ai/system/providers", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == "openai"

    resp = await client_with_domains.get(
        "/admin/ai/system/providers", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == [
        {
            "id": "default",
            "code": "openai",
            "base_url": "http://api.example",
            "health": "unknown",
        }
    ]

    payload["base_url"] = "http://api.changed"
    resp = await client_with_domains.post(
        "/admin/ai/system/providers", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["base_url"] == "http://api.changed"


@pytest.mark.asyncio
async def test_models_crud(
    client_with_domains: AsyncClient, admin_headers: dict[str, str], ai_tables: None
) -> None:
    resp = await client_with_domains.get(
        "/admin/ai/system/models", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []

    payload = {
        "code": "gpt-4",
        "provider": "openai",
        "name": "GPT-4",
        "active": True,
    }
    resp = await client_with_domains.post(
        "/admin/ai/system/models", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    model = resp.json()
    assert model["code"] == "gpt-4"
    assert model["active"] is True

    payload["active"] = False
    resp = await client_with_domains.post(
        "/admin/ai/system/models", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["active"] is False

    resp = await client_with_domains.get(
        "/admin/ai/system/models", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == [
        {
            "id": model["id"],
            "code": "gpt-4",
            "provider": "openai",
            "name": "GPT-4",
            "active": False,
        }
    ]


@pytest.mark.asyncio
async def test_prices_crud(
    client_with_domains: AsyncClient, admin_headers: dict[str, str], ai_tables: None
) -> None:
    resp = await client_with_domains.get(
        "/admin/ai/system/prices", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == []

    payload = {
        "model": "gpt-4",
        "input_cost": 0.003,
        "output_cost": 0.004,
        "currency": "USD",
    }
    resp = await client_with_domains.post(
        "/admin/ai/system/prices", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    price = resp.json()
    assert price["model"] == "gpt-4"

    payload.update({"input_cost": 0.005, "output_cost": 0.006})
    resp = await client_with_domains.post(
        "/admin/ai/system/prices", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["input_cost"] == 0.005

    resp = await client_with_domains.get(
        "/admin/ai/system/prices", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == [
        {
            "id": price["id"],
            "model": "gpt-4",
            "input_cost": 0.005,
            "output_cost": 0.006,
            "currency": "USD",
        }
    ]


@pytest.mark.asyncio
async def test_defaults_crud(
    client_with_domains: AsyncClient, admin_headers: dict[str, str], ai_tables: None
) -> None:
    resp = await client_with_domains.get(
        "/admin/ai/system/defaults", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == {}

    payload = {"provider": "openai", "model": "gpt-4"}
    resp = await client_with_domains.post(
        "/admin/ai/system/defaults", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    default = resp.json()
    assert default["provider"] == "openai"

    resp = await client_with_domains.get(
        "/admin/ai/system/defaults", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json() == default

    payload["model"] = "gpt-3.5"
    resp = await client_with_domains.post(
        "/admin/ai/system/defaults", json=payload, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["model"] == "gpt-3.5"
