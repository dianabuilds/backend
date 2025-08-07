"""
Вспомогательные функции для тестов.
"""
import os
from pathlib import Path
import tempfile
from typing import Set

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.dialects.postgresql import JSONB as pg_JSONB

# Список таблиц, которые необходимо создать для тестов
REQUIRED_TABLES = {'users'}

# Типы данных, которые нужно заменить в SQLite
TYPE_MAPPINGS = {
    'JSONB': 'TEXT',
    'UUID': 'CHAR(36)'
}

def get_db_url():
    """
    Возвращает URL для тестовой базы данных.
    По умолчанию использует SQLite в памяти.
    """
    db_url = os.environ.get("TEST_DATABASE_URL")
    if db_url:
        return db_url

    # Если URL не указан, используем SQLite в памяти
    return "sqlite+aiosqlite:///:memory:"

def is_sqlite(db_url: str) -> bool:
    """Проверяет, является ли URL адресом SQLite базы данных."""
    return db_url.startswith('sqlite')

async def create_test_tables(engine: AsyncEngine, tables: Set[str] = REQUIRED_TABLES):
    """
    Создает только необходимые для тестов таблицы.

    Args:
        engine: SQLAlchemy Engine для создания таблиц
        tables: Набор имен таблиц, которые нужно создать
    """
    # SQL для создания таблицы users
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id CHAR(36) PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        email VARCHAR UNIQUE,
        password_hash VARCHAR,
        wallet_address VARCHAR UNIQUE,
        is_active BOOLEAN DEFAULT 1,
        is_premium BOOLEAN DEFAULT 0,
        username VARCHAR UNIQUE NOT NULL,
        bio TEXT,
        avatar_url VARCHAR,
        deleted_at TIMESTAMP
    )
    """

    async with engine.begin() as conn:
        if 'users' in tables:
            await conn.execute(users_table_sql)

        # Здесь можно добавить другие таблицы по мере необходимости
        # if 'other_table' in tables:
        #     await conn.execute(other_table_sql)

    return True

def create_test_db_file():
    """
    Создает временный файл для SQLite базы данных.
    """
    temp_dir = tempfile.gettempdir()
    db_file = Path(temp_dir) / "test_fastapi.db"

    # Удаляем файл, если он существует
    if db_file.exists():
        db_file.unlink()

    return f"sqlite+aiosqlite:///{db_file}"

def get_table_names(engine):
    """
    Возвращает список имен таблиц в базе данных.
    """
    inspector = inspect(engine)
    return inspector.get_table_names()
