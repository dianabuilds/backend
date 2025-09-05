"""
Модуль для управления тестовой базой данных без использования SQLAlchemy ORM.
Это позволяет избежать проблем с несовместимыми типами данных.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text


def get_db_name() -> str:
    return os.getenv("DATABASE__NAME", "project_test")


def get_db_path() -> Path:
    return Path(f"../{get_db_name()}.db")


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
    default_workspace_id TEXT,
    last_login_at TIMESTAMP,
    deleted_at TIMESTAMP
)
"""

CREATE_USER_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS user_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
"""

CREATE_USER_RESTRICTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS user_restrictions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    issued_by TEXT
)
"""

# Индексы для таблицы users
USER_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
    "CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address)",
]

CREATE_WORKSPACES_TABLE = """
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_user_id TEXT NOT NULL,
    settings_json TEXT DEFAULT '{}',
    type TEXT NOT NULL DEFAULT 'team',
    is_system INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_WORKSPACE_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    permissions_json TEXT DEFAULT '{}',
    PRIMARY KEY (workspace_id, user_id)
)
"""

CREATE_ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_user_id TEXT NOT NULL,
    settings_json TEXT DEFAULT '{}',
    kind TEXT NOT NULL DEFAULT 'team',
    is_system INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_ACCOUNT_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS account_members (
    account_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    permissions_json TEXT DEFAULT '{}',
    PRIMARY KEY (account_id, user_id)
)
"""

CREATE_AI_USAGE_TABLE = """
CREATE TABLE IF NOT EXISTS ai_usage (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    user_id TEXT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    provider TEXT,
    model TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost REAL
)
"""

CREATE_BACKGROUND_JOB_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS background_job_history (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    log_url TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
)
"""


def setup_test_db():
    """Создает тестовую базу данных SQLite и необходимые таблицы."""
    db_path = get_db_path()

    # Удаляем старую БД, если она существует
    if db_path.exists():
        db_path.unlink()

    # Создаем соединение с базой данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицу users
    cursor.execute(CREATE_USERS_TABLE)
    cursor.execute(CREATE_USER_TOKENS_TABLE)
    cursor.execute(CREATE_USER_RESTRICTIONS_TABLE)
    cursor.execute(CREATE_WORKSPACES_TABLE)
    cursor.execute(CREATE_WORKSPACE_MEMBERS_TABLE)
    cursor.execute(CREATE_ACCOUNTS_TABLE)
    cursor.execute(CREATE_ACCOUNT_MEMBERS_TABLE)
    cursor.execute(CREATE_AI_USAGE_TABLE)
    cursor.execute(CREATE_BACKGROUND_JOB_HISTORY_TABLE)

    # Создаем индексы
    for index_sql in USER_INDEXES:
        cursor.execute(index_sql)

    # Закрываем соединение
    conn.commit()
    conn.close()

    print(f"Тестовая база данных создана: {db_path.absolute()}")
    return True


def get_db_url() -> str:
    """Возвращает URL для подключения к тестовой базе данных."""
    return f"sqlite+aiosqlite:///{get_db_path().absolute()}"


class TestUser:
    """
    Класс для работы с пользователями в тестовой базе данных.
    Заменяет модель User из основного приложения.
    """

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", str(uuid.uuid4()))
        self.created_at = kwargs.get("created_at", datetime.utcnow())
        self.email = kwargs.get("email")
        self.password_hash = kwargs.get("password_hash")
        self.wallet_address = kwargs.get("wallet_address")
        self.is_active = kwargs.get("is_active", True)
        self.is_premium = kwargs.get("is_premium", False)
        self.username = kwargs.get("username")
        self.bio = kwargs.get("bio")
        self.avatar_url = kwargs.get("avatar_url")
        self.role = kwargs.get("role", "user")
        self.default_workspace_id = kwargs.get("default_workspace_id")
        self.last_login_at = kwargs.get("last_login_at")
        self.deleted_at = kwargs.get("deleted_at")

    @staticmethod
    def from_row(row: tuple) -> "TestUser":
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
            username=row[8],
            bio=row[9],
            avatar_url=row[10],
            role=row[11],
            default_workspace_id=row[12],
            last_login_at=row[13],
            deleted_at=row[14],
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Преобразует объект в словарь.
        """
        return {
            "id": self.id,
            "created_at": (
                self.created_at.isoformat()
                if isinstance(self.created_at, datetime)
                else self.created_at
            ),
            "email": self.email,
            "password_hash": self.password_hash,
            "wallet_address": self.wallet_address,
            "is_active": 1 if self.is_active else 0,
            "is_premium": 1 if self.is_premium else 0,
            "username": self.username,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "role": self.role,
            "default_workspace_id": self.default_workspace_id,
            "last_login_at": (
                self.last_login_at.isoformat()
                if isinstance(self.last_login_at, datetime) and self.last_login_at
                else None
            ),
            "deleted_at": (
                self.deleted_at.isoformat()
                if isinstance(self.deleted_at, datetime) and self.deleted_at
                else None
            ),
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


async def get_user_by_username(username: str, conn) -> TestUser | None:
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
