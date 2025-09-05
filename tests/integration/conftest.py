"""
Минимальная конфигурация для тестов без использования SQLAlchemy ORM.
"""

import asyncio
import importlib
import os
import sys
import types
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from tests.integration.db_utils import TestUser, get_db_url, setup_test_db

# Устанавливаем переменные окружения для тестов
os.environ["TESTING"] = "True"
os.environ["ENV_MODE"] = "test"
os.environ["DATABASE__USERNAME"] = "testuser"
os.environ["DATABASE__PASSWORD"] = "testpass"
os.environ["DATABASE__HOST"] = "localhost"
os.environ["DATABASE__PORT"] = "5432"
os.environ["DATABASE__NAME"] = "project_test"
os.environ["JWT__SECRET"] = "test-secret-key"
os.environ["PAYMENT__JWT_SECRET"] = "test-payment-secret"
os.environ["REDIS_URL"] = "fakeredis://"
os.environ["CACHE__REDIS_URL"] = "fakeredis://"
os.environ["CORS_ALLOW_ORIGINS"] = '["https://example.com", "http://client.example"]'
os.environ["CORS_ALLOW_HEADERS"] = (
    '["X-Custom-Header", "Authorization", "Content-Type", "X-CSRF-Token", '
    '"X-CSRFToken", "X-Requested-With", "Workspace-Id", "X-Workspace-Id", '
    '"X-Feature-Flags", "X-Preview-Token", "X-BlockSketch-Workspace-Id"]'
)

# Инициализируем тестовую базу данных и формируем URL
setup_test_db()
os.environ["DATABASE_URL"] = get_db_url()

# Импортируем приложение после подготовки окружения
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

# Создаем тестовый движок и сессию
TEST_DB_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(
    TEST_DB_URL, echo=False, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает сессию базы данных для тестов."""
    async with TestingSessionLocal() as session:
        yield session

        # Очищаем данные после теста
        try:
            await session.execute(text("DELETE FROM account_members"))
            await session.execute(text("DELETE FROM accounts"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
        except Exception as err:
            _ = err
            await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Создает тестовый клиент."""
    # Stub workspace service for minimal config
    service_module = types.ModuleType("app.domains.workspaces.application.service")

    class _WS:
        @staticmethod
        async def create(db, *, data, owner):  # noqa: ANN001
            import uuid
            from types import SimpleNamespace

            from sqlalchemy import text

            ws_id = str(uuid.uuid4())
            await db.execute(
                text(
                    "INSERT INTO workspaces (id, name, slug, owner_user_id, type, "
                    "is_system, settings_json) "
                    "VALUES (:id, :name, :slug, :owner_id, :type, 0, '{}')"
                ),
                {
                    "id": ws_id,
                    "name": data.name,
                    "slug": data.slug,
                    "owner_id": str(owner.id),
                    "type": getattr(data.kind, "value", data.kind),
                },
            )
            await db.execute(
                text(
                    "INSERT INTO workspace_members (workspace_id, user_id, role) "
                    "VALUES (:ws_id, :user_id, 'owner')"
                ),
                {
                    "ws_id": ws_id,
                    "user_id": str(owner.id),
                },
            )
            await db.commit()
            return SimpleNamespace(id=ws_id, slug=data.slug)

    service_module.WorkspaceService = _WS
    service_module.require_ws_editor = lambda *args, **kwargs: None
    service_module.require_ws_guest = lambda *args, **kwargs: None
    service_module.require_ws_owner = lambda *args, **kwargs: None
    service_module.require_ws_viewer = lambda *args, **kwargs: None
    service_module.bearer_scheme = None

    application_pkg = types.ModuleType("app.domains.workspaces.application")
    application_pkg.service = service_module

    dao_module = types.ModuleType("app.domains.workspaces.infrastructure.dao")
    dao_module.WorkspaceDAO = type("WorkspaceDAO", (), {})
    infrastructure_pkg = types.ModuleType("app.domains.workspaces.infrastructure")
    infrastructure_pkg.dao = dao_module

    limits_module = types.ModuleType("app.domains.workspaces.limits")

    def _workspace_limit(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    limits_module.workspace_limit = _workspace_limit

    workspaces_pkg = types.ModuleType("app.domains.workspaces")
    workspaces_pkg.application = application_pkg
    workspaces_pkg.infrastructure = infrastructure_pkg
    workspaces_pkg.limits = limits_module

    sys.modules.update(
        {
            "app.domains.workspaces": workspaces_pkg,
            "app.domains.workspaces.application": application_pkg,
            "app.domains.workspaces.application.service": service_module,
            "app.domains.workspaces.infrastructure": infrastructure_pkg,
            "app.domains.workspaces.infrastructure.dao": dao_module,
            "app.domains.workspaces.limits": limits_module,
        }
    )

    # Stub ops router to avoid workspace dependencies
    from fastapi import APIRouter

    sys.modules.setdefault("app.api.ops", types.SimpleNamespace(router=APIRouter()))

    from apps.backend.app.main import app

    from app.providers.db.session import get_db

    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> TestUser:
    """Создает тестового пользователя."""
    from apps.backend.app.core.security import get_password_hash

    # Создаем тестового пользователя напрямую через SQL
    user = TestUser(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("Password123"),
        is_active=True,
        is_premium=False,
    )

    # Вставляем пользователя в базу данных
    user_dict = user.to_dict()
    columns = ", ".join(user_dict.keys())
    placeholders = ", ".join(f":{key}" for key in user_dict.keys())

    sql = text(f"INSERT INTO users ({columns}) VALUES ({placeholders})")
    await db_session.execute(sql, user_dict)
    await db_session.commit()

    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: TestUser) -> dict[str, str]:
    """Получает заголовки авторизации для тестового пользователя."""
    from apps.backend.app.core.security import create_access_token

    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
