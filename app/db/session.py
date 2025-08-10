import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)

# Кэш для хранения экземпляра движка
_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """
    Создаёт и кэширует экземпляр движка базы данных.
    Используется синглтон для повторного использования.
    """
    global _engine
    if _engine is None:
        logger.info(f"Creating database engine for environment: {settings.environment}")
        _engine = create_async_engine(
            settings.database_url,
            connect_args=settings.db_connect_args,
            **settings.db_pool_settings
        )

        if settings.logging.slow_query_ms:
            @event.listens_for(_engine.sync_engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: D401
                context._query_start_time = time.perf_counter()

            @event.listens_for(_engine.sync_engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # noqa: D401
                total = (time.perf_counter() - context._query_start_time) * 1000
                if total >= settings.logging.slow_query_ms:
                    logger.warning(
                        "SLOW SQL %.2fms: %s %s",
                        total,
                        statement,
                        parameters,
                    )
    return _engine


# Создаём фабрику сессий для асинхронной работы с БД
def get_session_factory():
    """Создаёт фабрику сессий для работы с базой данных"""
    engine = get_engine()
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI для получения сессии базы данных.
    Автоматически управляет жизненным циклом сессии.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def db_session():
    """
    Контекстный менеджер для использования сессии БД вне FastAPI зависимостей.
    Удобно для использования в фоновых задачах и скриптах.

    Пример:
    async with db_session() as session:
        result = await session.execute(...)
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error in context manager: {str(e)}")
        raise
    finally:
        await session.close()


async def run_migrations() -> None:
    """Apply database migrations using Alembic if migration scripts are present."""
    if not Path("alembic").exists():
        raise FileNotFoundError("alembic directory not found")

    loop = asyncio.get_running_loop()

    def _upgrade() -> None:
        cfg = Config("alembic.ini")
        cfg.set_main_option(
            "sqlalchemy.url", settings.database_url.replace("asyncpg", "psycopg2")
        )
        command.upgrade(cfg, "head")

    await loop.run_in_executor(None, _upgrade)
    logger.info("Alembic migrations applied")


async def create_tables() -> None:
    """Create all tables based on the SQLAlchemy models."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def init_db() -> None:
    """Initialize database by running migrations or creating tables."""
    try:
        await run_migrations()
    except Exception as e:
        logger.warning(f"Migrations not applied ({e}). Falling back to create_all().")
        await create_tables()


async def check_database_connection(max_retries: int = 5) -> bool:
    """
    Проверяет подключение к базе данных с механизмом повторных попыток.
    Полезно при запуске приложения для ожидания готовности БД.
    """
    engine = get_engine()
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Проверяем соединение
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except OperationalError as e:
            retry_count += 1
            wait_time = min(2 ** retry_count, 30)  # Экспоненциальная задержка, максимум 30 секунд

            logger.warning(
                f"Database connection attempt {retry_count}/{max_retries} failed: {str(e)}. "
                f"Retrying in {wait_time} seconds..."
            )

            await asyncio.sleep(wait_time)

    logger.error(f"Failed to connect to database after {max_retries} attempts")
    return False


async def close_db_connection():
    """Закрывает соединения с базой данных при остановке приложения"""
    global _engine
    if _engine is not None:
        logger.info("Closing database connections")
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
