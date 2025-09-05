import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.providers.db.base import Base

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_ctx: ContextVar[AsyncSession | None] = ContextVar("db_session", default=None)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        logger.info(
            f"Creating database engine for environment: {settings.env_mode}"
            f" (database: {settings.database_name})"
        )
        _engine = create_async_engine(
            settings.database_url,
            connect_args=settings.db_connect_args,
            **settings.db_pool_settings,
        )

        if settings.logging.slow_query_ms:

            @event.listens_for(_engine.sync_engine, "before_cursor_execute")
            def before_cursor_execute(
                conn, cursor, statement, parameters, context, executemany
            ):  # noqa: D401
                context._query_start_time = time.perf_counter()

            @event.listens_for(_engine.sync_engine, "after_cursor_execute")
            def after_cursor_execute(
                conn, cursor, statement, parameters, context, executemany
            ):  # noqa: D401
                total = (time.perf_counter() - context._query_start_time) * 1000
                if total >= settings.logging.slow_query_ms:
                    logger.warning(
                        "SLOW SQL %.2fms: %s %s",
                        total,
                        statement,
                        parameters,
                    )

    return _engine


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


def get_current_session() -> AsyncSession | None:
    return _session_ctx.get()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
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
    cfg = Config("alembic.ini")
    script_location = Path(cfg.get_main_option("script_location", "alembic"))
    if not script_location.exists():
        raise FileNotFoundError(f"{script_location} directory not found")

    loop = asyncio.get_running_loop()

    def _upgrade() -> None:
        cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("asyncpg", "psycopg2"))
        command.upgrade(cfg, "heads")

    await loop.run_in_executor(None, _upgrade)
    logger.info("Alembic migrations applied")


async def create_tables() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def ensure_min_schema() -> None:
    logger.info("ensure_min_schema: skipped (schema is managed by Alembic only)")
    return


async def init_db() -> None:
    try:
        await run_migrations()
    except Exception as e:
        logger.warning(f"Migrations not applied ({e}). Falling back to create_all().")
        await create_tables()
    await ensure_min_schema()


async def check_database_connection(max_retries: int = 5) -> bool:
    engine = get_engine()
    retry_count = 0

    while retry_count < max_retries:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except OperationalError as e:
            retry_count += 1
            wait_time = min(2**retry_count, 30)
            logger.warning(
                "Database connection attempt %s/%s failed: %s. " "Retrying in %s seconds...",
                retry_count,
                max_retries,
                str(e),
                wait_time,
            )
            await asyncio.sleep(wait_time)
        except SQLAlchemyError as e:
            logger.error("Database connection error: %s", str(e))
            return False

    logger.error(f"Failed to connect to database after {max_retries} attempts")
    return False


async def close_db_connection():
    global _engine
    if _engine is not None:
        logger.info("Closing database connections")
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")
