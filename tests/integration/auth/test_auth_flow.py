"""Минимальный тест для авторизации, который не зависит от SQLAlchemy ORM."""

from __future__ import annotations

import os
import types

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Устанавливаем флаг для использования минимальной конфигурации
os.environ["USE_MINIMAL_CONFIG"] = "True"


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, db_session: AsyncSession):
    """Проверка успешной регистрации."""
    # Данные для регистрации
    signup_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "Password123",
    }

    # Выполняем запрос на регистрацию
    response = await client.post("/auth/signup", json=signup_data)

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "verification_token" in data

    # Проверяем, что пользователь создан в БД, используя сырой SQL запрос
    sql = text("SELECT email, is_active FROM users WHERE username = :username")
    result = await db_session.execute(sql, {"username": "newuser"})
    user = result.fetchone()

    assert user is not None
    assert user[0] == "newuser@example.com"
    assert not user[1]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Проверка успешного входа в систему."""
    # Данные для входа
    login_data = {"username": "testuser", "password": "Password123"}

    # Выполняем запрос на вход
    response = await client.post("/auth/login", json=login_data)

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_login_returns_tokens(client: AsyncClient, test_user):
    """Возвращает access и refresh токены для валидного логина."""
    login_data = {"username": "testuser", "password": "Password123"}
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token")
    assert response.cookies.get("refresh_token")


@pytest.mark.asyncio
async def test_login_form_success(client: AsyncClient, test_user):
    """Проверка входа через form-data."""
    login_data = {"username": "testuser", "password": "Password123"}
    response = await client.post(
        "/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_login_alias_signin(client: AsyncClient, test_user):
    login_data = {"username": "testuser", "password": "Password123"}
    resp = await client.post("/auth/signin", json=login_data)
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_renews_tokens(client: AsyncClient, test_user):
    login_data = {"username": "testuser", "password": "Password123"}
    resp = await client.post("/auth/login", json=login_data)
    assert resp.status_code == 200
    old_access = resp.json()["access_token"]
    assert resp.cookies.get("refresh_token") is not None

    resp2 = await client.post("/auth/refresh")
    assert resp2.status_code == 200
    data = resp2.json()
    assert "access_token" in data
    assert resp2.cookies.get("refresh_token") is not None
    assert data["access_token"] != old_access


@pytest.mark.asyncio
async def test_refresh_alias_root(client: AsyncClient, test_user):
    login_data = {"username": "testuser", "password": "Password123"}
    resp = await client.post("/auth/login", json=login_data)
    assert resp.status_code == 200
    old_access = resp.json()["access_token"]
    assert resp.cookies.get("refresh_token") is not None

    resp2 = await client.post("/refresh")
    assert resp2.status_code == 200
    data = resp2.json()
    assert "access_token" in data
    assert resp2.cookies.get("refresh_token") is not None
    assert data["access_token"] != old_access


@pytest.mark.asyncio
async def test_login_uses_json_rate_limit_rule(
    client: AsyncClient, test_user, monkeypatch
):
    used: dict[str, str] = {}

    async def dummy_dep(request, response):  # noqa: ANN001
        return None

    def fake_dependency(key: str):
        used["key"] = key
        return dummy_dep

    from app.domains.auth.api import auth_router

    monkeypatch.setattr(
        auth_router, "_rate", types.SimpleNamespace(dependency=fake_dependency)
    )
    login_data = {"username": "testuser", "password": "Password123"}
    await client.post("/auth/login", json=login_data)
    assert used["key"] == "login_json"
