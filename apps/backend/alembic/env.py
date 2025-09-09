import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool

from alembic import context

config = context.config

# Ensure backend package is on sys.path so we can import application modules
sys.path.insert(
    0,
    str(
        Path(config.config_file_name).resolve().parent / config.get_main_option("prepend_sys_path")
    ),
)

fileConfig(config.config_file_name)

from app.core.env_loader import load_dotenv  # noqa: E402

# Load environment variables from .env before importing settings
load_dotenv()

from app.core.config import settings  # noqa: E402
from app.providers.db.base import Base  # noqa: E402

target_metadata = Base.metadata


def _sync_sqlalchemy_url() -> str:
    """Build a synchronous SQLAlchemy URL suitable for Alembic.

    The app uses asyncpg (postgresql+asyncpg). Alembic runs with a sync engine,
    so we drop the "+asyncpg" suffix. If SSL is required (e.g. managed
    Postgres), ensure we pass sslmode=require for psycopg2.
    """
    url = settings.database_url.replace("+asyncpg", "")
    if url.startswith("postgresql://") and "sslmode=" not in url:
        try:
            from app.core.app_settings.database import DatabaseSettings  # type: ignore

            # If configuration requires SSL, append sslmode=require for psycopg2
            if settings.database.sslmode == "require":
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}sslmode=require"
        except Exception:
            # Best effort; if anything goes wrong, keep the original URL
            pass
    return url


def run_migrations_offline():
    url = _sync_sqlalchemy_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = _sync_sqlalchemy_url()
    # Не читаем секцию из alembic.ini, чтобы избежать configparser interpolation errors.
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
