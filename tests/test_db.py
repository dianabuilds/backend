"""
Модуль для управления тестовой базой данных без использования SQLAlchemy ORM.
Это позволяет избежать проблем с несовместимыми типами данных.
"""
import os
import uuid
import sqlite3
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import text


# Путь к тестовой базе данных
TEST_DB_PATH = "../test.db"

# SQL для создания таблицы users
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email TEXT UNIQUE,
    password_hash TEXT,
    wallet_address TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    is_premium INTEGER DEFAULT 0,
    premium_until TIMESTAMP,
    username TEXT UNIQUE NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'user',
    deleted_at TIMESTAMP
)
"""

# Индексы для таблицы users
USER_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
    "CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address)"
]


def setup_test_db():
    """
    Создает тестовую базу данных SQLite и необходимые таблицы.
    """
    db_path = Path(TEST_DB_PATH)

    # Удаляем старую БД, если она существует
    if db_path.exists():
        db_path.unlink()

    # Создаем соединение с базой данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицу users
    cursor.execute(CREATE_USERS_TABLE)

    # Создаем индексы
    for index_sql in USER_INDEXES:
        cursor.execute(index_sql)

    # Закрываем соединение
    conn.commit()
    conn.close()

    print(f"Тестовая база данных создана: {db_path.absolute()}")
    return True


def get_db_url():
    """
    Возвращает URL для подключения к тестовой базе данных.
    """
    db_path = Path(TEST_DB_PATH).absolute()
    return f"sqlite+aiosqlite:///{db_path}"


class TestUser:
    """
    Класс для работы с пользователями в тестовой базе данных.
    Заменяет модель User из основного приложения.
    """
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.wallet_address = kwargs.get('wallet_address')
        self.is_active = kwargs.get('is_active', True)
        self.is_premium = kwargs.get('is_premium', False)
        self.username = kwargs.get('username')
        self.bio = kwargs.get('bio')
        self.avatar_url = kwargs.get('avatar_url')
        self.role = kwargs.get('role', 'user')
        self.deleted_at = kwargs.get('deleted_at')

    @staticmethod
    def from_row(row: tuple) -> 'TestUser':
        """
        Создает объект TestUser из строки результата запроса.
        """
        return TestUser(
            id=row[0],
            created_at=row[1],
            email=row[2],
            password_hash=row[3],
            wallet_address=row[4],
            is_active=bool(row[5]),
            is_premium=bool(row[6]),
            username=row[7],
            bio=row[8],
            avatar_url=row[10],
            role=row[11],
            deleted_at=row[12]
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует объект в словарь.
        """
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'email': self.email,
            'password_hash': self.password_hash,
            'wallet_address': self.wallet_address,
            'is_active': 1 if self.is_active else 0,
            'is_premium': 1 if self.is_premium else 0,
            'username': self.username,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'deleted_at': self.deleted_at.isoformat() if isinstance(self.deleted_at, datetime) and self.deleted_at else None
        }


async def create_user(user: TestUser, conn) -> bool:
    """
    Создает пользователя в базе данных.
    """
    user_dict = user.to_dict()

    # Создаем SQL запрос
    columns = ", ".join(user_dict.keys())
    placeholders = ", ".join(f":{key}" for key in user_dict.keys())

    sql = text(f"INSERT INTO users ({columns}) VALUES ({placeholders})")

    try:
        await conn.execute(sql, user_dict)
        await conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при создании пользователя: {str(e)}")
        await conn.rollback()
        return False


async def get_user_by_username(username: str, conn) -> Optional[TestUser]:
    """
    Получает пользователя по имени пользователя.
    """
    sql = text("SELECT * FROM users WHERE username = :username")

    try:
        result = await conn.execute(sql, {"username": username})
        row = await result.fetchone()

        if row:
            # Преобразуем в dict для более удобного доступа к полям
            columns = [col[0] for col in result.description]
            user_dict = {columns[i]: row[i] for i in range(len(columns))}

            return TestUser(**user_dict)

        return None
    except Exception as e:
        print(f"Ошибка при получении пользователя: {str(e)}")
        return None


# Инициализация базы данных при импорте модуля
if __name__ == "__main__":
    setup_test_db()
