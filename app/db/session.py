import asyncio
import logging
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar
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
_session_ctx: ContextVar[AsyncSession | None] = ContextVar("db_session", default=None)


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


def get_current_session() -> AsyncSession | None:
    return _session_ctx.get()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI для получения сессии базы данных.
    Автоматически управляет жизненным циклом сессии.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        token = _session_ctx.set(session)
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            _session_ctx.reset(token)
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
        # Используем 'heads', чтобы применить все ветки, если они вдруг появятся
        command.upgrade(cfg, "heads")

    await loop.run_in_executor(None, _upgrade)
    logger.info("Alembic migrations applied")


async def create_tables() -> None:
    """Create all tables based on the SQLAlchemy models."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def ensure_min_schema() -> None:
    """
    Минимальное выравнивание схемы на случай, если Alembic не выполнился
    (например, из-за hot-reload). Безопасно повторяется.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        try:
            # Добавляем столбец cover_url у nodes, если его нет
            await conn.execute(text("ALTER TABLE IF EXISTS nodes ADD COLUMN IF NOT EXISTS cover_url TEXT"))
            # Обеспечиваем наличие столбца search_vector у quests (тип зависит от диалекта)
            try:
                if getattr(conn.dialect, "name", "") == "postgresql":
                    await conn.execute(text("ALTER TABLE IF EXISTS quests ADD COLUMN IF NOT EXISTS search_vector TSVECTOR"))
                else:
                    await conn.execute(text("ALTER TABLE IF EXISTS quests ADD COLUMN IF NOT EXISTS search_vector TEXT"))
            except Exception as se:
                logger.warning(f"ensure_min_schema quests.search_vector failed: {se}")
            # Создаём таблицу feature_flags, если её нет
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS feature_flags (
                        key TEXT PRIMARY KEY,
                        value BOOLEAN NOT NULL DEFAULT FALSE,
                        description TEXT NULL,
                        updated_at TIMESTAMP NULL,
                        updated_by TEXT NULL
                    )
                    """
                )
            )
            # Минимальные таблицы модерации (если нет Alembic)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS moderation_cases (
                    id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    reporter_id TEXT NULL,
                    reporter_contact TEXT NULL,
                    target_type TEXT NULL,
                    target_id TEXT NULL,
                    summary TEXT NOT NULL,
                    details TEXT NULL,
                    assignee_id TEXT NULL,
                    due_at TIMESTAMP NULL,
                    first_response_due_at TIMESTAMP NULL,
                    last_event_at TIMESTAMP NULL,
                    source TEXT NULL,
                    reason_code TEXT NULL,
                    resolution TEXT NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS moderation_labels (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT NULL,
                    protected BOOLEAN NOT NULL DEFAULT FALSE
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS case_labels (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
                    label_id TEXT NOT NULL REFERENCES moderation_labels(id) ON DELETE CASCADE
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS case_notes (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
                    author_id TEXT NULL,
                    created_at TIMESTAMP NOT NULL,
                    text TEXT NOT NULL,
                    internal BOOLEAN NOT NULL DEFAULT TRUE
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS case_attachments (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
                    author_id TEXT NULL,
                    created_at TIMESTAMP NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NULL,
                    media_type TEXT NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS case_events (
                    id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
                    actor_id TEXT NULL,
                    created_at TIMESTAMP NOT NULL,
                    kind TEXT NOT NULL,
                    payload TEXT NULL
                );
            """))
            # Таблицы конфигураций поиска (версии и активная релевантность)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS config_versions (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    created_by TEXT NULL,
                    parent_id TEXT NULL,
                    comment TEXT NULL,
                    checksum TEXT NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS search_relevance_active (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    updated_by TEXT NULL
                );
            """))
            # Таблицы управления тегами (алиасы, логи слияний)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tag_aliases (
                    id TEXT PRIMARY KEY,
                    tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                    alias TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tag_merge_logs (
                    id TEXT PRIMARY KEY,
                    from_tag_id TEXT NOT NULL,
                    to_tag_id TEXT NOT NULL,
                    merged_by TEXT NULL,
                    merged_at TIMESTAMP NOT NULL,
                    dry_run BOOLEAN NOT NULL DEFAULT FALSE,
                    reason TEXT NULL,
                    report TEXT NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tag_blacklist (
                    slug TEXT PRIMARY KEY,
                    reason TEXT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            """))
            # Таблицы редактора квестов
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quest_versions (
                    id TEXT PRIMARY KEY,
                    quest_id TEXT NOT NULL,
                    number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    created_by TEXT NULL,
                    released_at TIMESTAMP NULL,
                    released_by TEXT NULL,
                    parent_version_id TEXT NULL,
                    meta TEXT NULL
                );
            """))
            await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_quest_version_number ON quest_versions (quest_id, number);"))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quest_graph_nodes (
                    id TEXT PRIMARY KEY,
                    version_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NULL,
                    rewards TEXT NULL
                );
            """))
            await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_qnode_key ON quest_graph_nodes (version_id, key);"))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quest_graph_edges (
                    id TEXT PRIMARY KEY,
                    version_id TEXT NOT NULL,
                    from_node_key TEXT NOT NULL,
                    to_node_key TEXT NOT NULL,
                    label TEXT NULL,
                    condition TEXT NULL
                );
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quest_draft_locks (
                    id TEXT PRIMARY KEY,
                    version_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
            """))
        except Exception as e:
            logger.warning(f"ensure_min_schema failed: {e}")


async def init_db() -> None:
    """Initialize database by running migrations or creating tables."""
    try:
        await run_migrations()
    except Exception as e:
        logger.warning(f"Migrations not applied ({e}). Falling back to create_all().")
        await create_tables()
    # Гарантируем наличие критически важных колонок даже при сбое Alembic
    await ensure_min_schema()


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
