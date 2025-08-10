"""
Минимальный тест для авторизации, который не зависит от SQLAlchemy ORM.
"""
import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Устанавливаем флаг для использования минимальной конфигурации
os.environ["USE_MINIMAL_CONFIG"] = "True"

# Импортируем минимальную конфигурацию
from tests.conftest_minimal import client, db_session, test_user


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, db_session: AsyncSession):
    """Проверка успешной регистрации."""
    # Данные для регистрации
    signup_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "Password123"
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
    login_data = {
        "username": "testuser",
        "password": "Password123"
    }

    # Выполняем запрос на вход
    response = await client.post("/auth/login", json=login_data)

    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
