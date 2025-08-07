"""
Явный тест базовой инфраструктуры.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    """
    Проверка подключения к базе данных и создания таблицы users.
    """
    # Проверяем, что таблица users существует
    try:
        # Для SQLite
        tables_query = text("SELECT name FROM sqlite_master WHERE type='table'")
        tables_result = await db_session.execute(tables_query)
        tables = [row[0] for row in tables_result]
        print(f"Существующие таблицы: {tables}")

        assert 'users' in tables, "Таблица users не создана"

        # Проверяем структуру таблицы users
        schema_query = text("PRAGMA table_info(users)")
        schema_result = await db_session.execute(schema_query)
        columns = {row[1]: row[2] for row in schema_result}
        print(f"Структура таблицы users: {columns}")

        # Проверяем основные поля
        assert 'id' in columns, "Поле id отсутствует в таблице users"
        assert 'email' in columns, "Поле email отсутствует в таблице users"
        assert 'username' in columns, "Поле username отсутствует в таблице users"

        return True
    except Exception as e:
        print(f"Ошибка при тестировании базы данных: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_client_connection(client: AsyncClient):
    """
    Проверка подключения к API.
    """
    # Проверяем корневой эндпоинт
    response = await client.get("/")
    assert response.status_code == 200, "Не удалось получить ответ от корневого эндпоинта"

    # Проверяем, что ответ содержит ожидаемые данные
    data = response.json()
    assert "message" in data, "Ответ не содержит ожидаемого поля 'message'"

    return True
