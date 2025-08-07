import sys
from pathlib import Path
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("db_username", "u")
os.environ.setdefault("db_password", "p")
os.environ.setdefault("db_host", "localhost")
os.environ.setdefault("db_port", "5432")
os.environ.setdefault("db_name", "test")
os.environ.setdefault("jwt_secret", "secret")

from app.main import app
from app.api.deps import get_db
from app.models import Base, User
from app.core.security import create_access_token


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session: AsyncSession):
    async def _get_test_db():
        yield session
    app.dependency_overrides[get_db] = _get_test_db
    transport = httpx.ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(session: AsyncSession) -> User:
    user = User(email="u@example.com", username="user", password_hash="x")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_premium_endpoint_denied_without_subscription(client: AsyncClient, user: User):
    token = create_access_token(user.id)
    resp = await client.get("/nodes/test/echo", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Premium subscription required"


@pytest.mark.asyncio
async def test_set_premium_via_admin_api(client: AsyncClient, session: AsyncSession, user: User):
    token = create_access_token(user.id)
    payload = {"is_premium": True}
    resp = await client.post(
        f"/admin/users/{user.id}/premium",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    await session.refresh(user)
    assert user.is_premium is True


@pytest.mark.asyncio
async def test_premium_endpoint_allowed_with_subscription(client: AsyncClient, user: User, session: AsyncSession):
    token = create_access_token(user.id)
    await client.post(
        f"/admin/users/{user.id}/premium",
        json={"is_premium": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/nodes/test/echo", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200




@pytest.mark.asyncio
async def test_user_profile_does_not_expose_premium_fields(client: AsyncClient, user: User):
    token = create_access_token(user.id)
    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert "is_premium" not in data
    assert "premium_until" not in data
from contextlib import asynccontextmanager


@asynccontextmanager
async def _lifespan(app):
    yield


app.router.lifespan_context = _lifespan
