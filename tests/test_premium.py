"""
Тесты для функционала премиум-подписки.
"""
import logging
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import create_access_token


class TestPremium:
    """Тесты для API премиум-функционала."""

    @pytest.mark.asyncio
    async def test_premium_endpoint_denied_without_subscription(
        self, client: AsyncClient, test_user: User
    ):
        """Проверка, что премиум-эндпоинт недоступен без подписки."""
        # Получаем токен для тестового пользователя
        token = create_access_token(test_user.id)

        # Делаем запрос к премиум-эндпоинту
        response = await client.get(
            "/nodes/test/echo", 
            headers={"Authorization": f"Bearer {token}"}
        )

        # Проверяем, что доступ запрещен
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "FORBIDDEN"
        assert data["error"]["message"] == "Premium subscription required"

    @pytest.mark.asyncio
    async def test_set_premium_requires_admin(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        admin_user: User,
        caplog,
    ):
        """Проверка, что премиум может менять только админ и действие логируется."""
        user_token = create_access_token(test_user.id)
        response = await client.post(
            f"/admin/users/{test_user.id}/premium",
            json={"is_premium": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

        admin_token = create_access_token(admin_user.id)
        with caplog.at_level(logging.INFO):
            response = await client.post(
                f"/admin/users/{test_user.id}/premium",
                json={"is_premium": True},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200

        await db_session.refresh(test_user)
        assert test_user.is_premium is True
        assert any(getattr(rec, "action", None) == "set_premium" for rec in caplog.records)

    @pytest.mark.asyncio
    async def test_premium_endpoint_allowed_with_subscription(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
        admin_user: User,
    ):
        """Проверка, что премиум-эндпоинт доступен с подпиской."""
        # Получаем токен для тестового пользователя
        token = create_access_token(test_user.id)
        admin_token = create_access_token(admin_user.id)

        await client.post(
            f"/admin/users/{test_user.id}/premium",
            json={"is_premium": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Делаем запрос к премиум-эндпоинту
        response = await client.get(
            "/nodes/test/echo", 
            headers={"Authorization": f"Bearer {token}"}
        )

        # Проверяем успешный ответ
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_user_profile_does_not_expose_premium_fields(
        self, client: AsyncClient, test_user: User
    ):
        """Проверка, что профиль пользователя не содержит премиум-полей."""
        # Получаем токен для тестового пользователя
        token = create_access_token(test_user.id)

        # Запрашиваем профиль пользователя
        response = await client.get(
            "/users/me", 
            headers={"Authorization": f"Bearer {token}"}
        )

        # Проверяем ответ
        data = response.json()
        assert "is_premium" not in data
        assert "premium_until" not in data
