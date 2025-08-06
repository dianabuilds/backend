import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from app.core.config import settings

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
        logger.info(f"Creating database engine for environment: {settings.ENVIRONMENT}")
        _engine = create_async_engine(
            settings.database_url,
            connect_args=settings.db_connect_args,
            **settings.db_pool_settings
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
                await conn.execute("SELECT 1")
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
