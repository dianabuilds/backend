"""
Тесты для API пользователей.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.user import User


class TestUsers:
    """Тесты для API пользователей."""

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """Проверка получения текущего пользователя."""
        # Выполняем запрос на получение текущего пользователя
        response = await client.get("/users/me", headers=auth_headers)

        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Проверка получения текущего пользователя без авторизации."""
        # Выполняем запрос без заголовка авторизации
        response = await client.get("/users/me")

        # Проверяем ответ - должна быть ошибка авторизации
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_update_user(self, client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Проверка обновления данных пользователя."""
        # Данные для обновления пользователя
        update_data = {
            "username": "updateduser",
            "bio": "This is my new bio",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # Выполняем запрос на обновление
        response = await client.patch("/users/me", json=update_data, headers=auth_headers)

        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["bio"] == "This is my new bio"
        assert data["avatar_url"] == "https://example.com/avatar.jpg"

        # Проверяем, что данные обновились в БД
        user_query = await db_session.execute(text("SELECT * FROM users WHERE username = 'updateduser'"))
        user = user_query.first()
        assert user is not None
        assert user.bio == "This is my new bio"
