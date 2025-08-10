"""
Конфигурация для тестов.
Предоставляет фикстуры для тестирования API.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Generator

# Устанавливаем флаг тестирования
os.environ["TESTING"] = "True"
os.environ["PAYMENT_JWT_SECRET"] = "test-payment-secret"

from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.core.security import get_password_hash

# Импортируем вспомогательные функции
from tests.test_helpers import create_test_db_file

# Настройка тестовой базы данных
TEST_DB_URL = create_test_db_file()

# Создаем тестовый движок и сессию
test_engine = create_async_engine(
    TEST_DB_URL, 
    echo=False,
    # Эти параметры помогают избежать проблем с SQLite в тестах
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Увеличиваем таймаут для операций SQLite
    } if TEST_DB_URL.startswith("sqlite") else {}
)

TestingSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Создает event loop для тестов, который работает на протяжении всей сессии.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Создает сессию базы данных для тестов.
    Создает схему базы данных перед каждым тестом и удаляет ее после.
    """
    # Создаем таблицы для тестирования
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем сессию для теста
    async with TestingSessionLocal() as session:
        yield session

    # Удаляем таблицы после теста
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Создает тестовый клиент с переопределенной зависимостью базы данных.
    """
    # Переопределяем зависимость get_db для использования тестовой сессии
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Создаем тестовый клиент
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Удаляем переопределение зависимости
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    Создает тестового пользователя в базе данных.
    """
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("Password123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("Password123"),
        is_active=True,
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def moderator_user(db_session: AsyncSession) -> User:
    """Create a test moderator user."""
    user = User(
        email="moderator@example.com",
        username="moderator",
        password_hash=get_password_hash("Password123"),
        is_active=True,
        role="moderator",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    """
    Получает заголовки авторизации для тестового пользователя.
    """
    # Логинимся для получения токена
    response = await client.post(
        "/auth/login",
        json={"username": "testuser", "password": "Password123"}
    )
    token = response.json()["access_token"]

    # Возвращаем заголовки с токеном авторизации
    return {"Authorization": f"Bearer {token}"}
