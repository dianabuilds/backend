"""
Тесты для аутентификации и авторизации.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User


class TestAuth:
    """Тесты для API аутентификации и авторизации."""

    @pytest.mark.asyncio
    async def test_signup_success(self, client: AsyncClient, db_session: AsyncSession):
        """Проверка успешной регистрации."""
        # Диагностика: проверяем, что таблица users существует
        try:
            from sqlalchemy import text
            tables_query = text("SELECT name FROM sqlite_master WHERE type='table'")
            tables_result = await db_session.execute(tables_query)
            tables = [row[0] for row in tables_result]
            print(f"Существующие таблицы: {tables}")

            # Проверяем структуру таблицы users
            if 'users' in tables:
                schema_query = text("PRAGMA table_info(users)")
                schema_result = await db_session.execute(schema_query)
                columns = [(row[1], row[2]) for row in schema_result]
                print(f"Структура таблицы users: {columns}")
        except Exception as e:
            print(f"Ошибка при диагностике: {str(e)}")

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

        # Проверяем, что пользователь создан в БД и не активен
        try:
            query = text("SELECT * FROM users WHERE username = :username")
            result = await db_session.execute(query, {"username": "newuser"})
            user = result.first()
            assert user is not None
            assert user.email == "newuser@example.com"
            # is_active field is at index ? depends on schema; easier use ORM
            query2 = select(User).where(User.username == "newuser")
            result2 = await db_session.execute(query2)
            orm_user = result2.scalars().first()
            assert orm_user is not None and not orm_user.is_active
        except Exception as e:
            print(f"Ошибка при проверке пользователя: {str(e)}")
            raise

    @pytest.mark.asyncio
    async def test_signup_duplicate_username(self, client: AsyncClient, test_user: User):
        """Проверка регистрации с существующим именем пользователя."""
        # Данные для регистрации с существующим username
        signup_data = {
            "email": "another@example.com",
            "username": "testuser",  # Уже существует (из фикстуры test_user)
            "password": "Password123"
        }

        # Выполняем запрос на регистрацию
        response = await client.post("/auth/signup", json=signup_data)

        # Проверяем ответ - должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "username already taken" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(self, client: AsyncClient, test_user: User):
        """Проверка регистрации с существующим email."""
        # Данные для регистрации с существующим email
        signup_data = {
            "email": "test@example.com",  # Уже существует (из фикстуры test_user)
            "username": "anotheruser",
            "password": "Password123"
        }

        # Выполняем запрос на регистрацию
        response = await client.post("/auth/signup", json=signup_data)

        # Проверяем ответ - должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "email already registered" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_signup_invalid_data(self, client: AsyncClient):
        """Проверка регистрации с некорректными данными."""
        # Данные для регистрации с некорректным email
        signup_data = {
            "email": "not-an-email",
            "username": "newuser",
            "password": "Password123"
        }

        # Выполняем запрос на регистрацию
        response = await client.post("/auth/signup", json=signup_data)

        # Проверяем ответ - должна быть ошибка валидации
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_email_verification_flow(self, client: AsyncClient, db_session: AsyncSession):
        signup_data = {
            "email": "verify@example.com",
            "username": "verifyuser",
            "password": "Password123",
        }
        response = await client.post("/auth/signup", json=signup_data)
        assert response.status_code == 200
        token = response.json()["verification_token"]

        login_data = {"username": "verifyuser", "password": "Password123"}
        login_resp = await client.post("/auth/login", json=login_data)
        assert login_resp.status_code == 400

        verify_resp = await client.get(f"/auth/verify?token={token}")
        assert verify_resp.status_code == 200

        login_resp = await client.post("/auth/login", json=login_data)
        assert login_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
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

    @pytest.mark.asyncio
    async def test_login_wrong_username(self, client: AsyncClient, test_user: User):
        """Проверка входа с неправильным именем пользователя."""
        # Данные для входа с неправильным username
        login_data = {
            "username": "wronguser",
            "password": "Password123"
        }

        # Выполняем запрос на вход
        response = await client.post("/auth/login", json=login_data)

        # Проверяем ответ - должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "incorrect username or password" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Проверка входа с неправильным паролем."""
        # Данные для входа с неправильным паролем
        login_data = {
            "username": "testuser",
            "password": "WrongPassword"
        }

        # Выполняем запрос на вход
        response = await client.post("/auth/login", json=login_data)

        # Проверяем ответ - должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "incorrect username or password" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password(self, client: AsyncClient, auth_headers: dict):
        """Проверка изменения пароля."""
        # Данные для изменения пароля
        change_password_data = {
            "old_password": "Password123",
            "new_password": "NewPassword123"
        }

        # Выполняем запрос на изменение пароля
        response = await client.post(
            "/auth/change-password",
            json=change_password_data,
            headers=auth_headers
        )

        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "password updated" in data["message"].lower()

        # Проверяем, что можно войти с новым паролем
        login_data = {
            "username": "testuser",
            "password": "NewPassword123"
        }
        login_response = await client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
