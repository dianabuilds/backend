"""
Скрипт для создания таблиц в тестовой базе данных без использования SQLAlchemy ORM.
Это полный обход проблем с типами данных, несовместимыми с SQLite.
"""
import os
import asyncio
import sqlite3
from pathlib import Path

# Установка флага тестовой среды
os.environ["TESTING"] = "True"

# SQL для создания таблицы users в SQLite
CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email TEXT UNIQUE,
    password_hash TEXT,
    wallet_address TEXT UNIQUE,
    is_active INTEGER DEFAULT 1,
    is_premium INTEGER DEFAULT 0,
    username TEXT UNIQUE NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    deleted_at TIMESTAMP
)
"""

def create_test_db():
    """
    Создает тестовую базу данных SQLite и необходимые таблицы напрямую.
    """
    db_path = Path("./test.db")

    # Удаляем старую БД, если она существует
    if db_path.exists():
        db_path.unlink()

    # Создаем соединение с базой данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создаем таблицу users
    cursor.execute(CREATE_USERS_TABLE_SQL)

    # Создаем индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_wallet ON users(wallet_address)")

    # Закрываем соединение
    conn.commit()
    conn.close()

    print(f"Тестовая база данных создана: {db_path.absolute()}")
    return True

if __name__ == "__main__":
    create_test_db()
