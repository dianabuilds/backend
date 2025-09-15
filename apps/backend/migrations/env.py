from __future__ import annotations

import logging
from logging.config import fileConfig

import os
from urllib.parse import quote_plus
from alembic import context
from sqlalchemy import engine_from_config, pool

# Interpret the config file for Python logging.
config = context.config
# Load .env files so DATABASE__* and APP_DATABASE_URL are available
try:
    from dotenv import load_dotenv

    load_dotenv(".env")
    load_dotenv("apps/backend/.env")
except Exception:
    pass
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger(__name__)


def _get_db_url() -> str:
    """Resolve DB URL with sensible precedence after repo move.

    1) If APP_DATABASE_URL is set (env/.env), use it.
    2) Else, use sqlalchemy.url from alembic.ini (supports DATABASE__* vars).
    """
    app_url = os.getenv("APP_DATABASE_URL")
    if app_url:
        return app_url

    # Compose from DATABASE__* pieces if provided in environment/.env
    user = os.getenv("DATABASE__USERNAME")
    host = os.getenv("DATABASE__HOST")
    name = os.getenv("DATABASE__NAME")
    if user and host and name:
        password = os.getenv("DATABASE__PASSWORD", "")
        port = os.getenv("DATABASE__PORT", "5432")
        sslmode = os.getenv("DATABASE__SSLMODE")
        pw = f":{quote_plus(password)}" if password else ""
        query = f"?sslmode={sslmode}" if sslmode else ""
        return f"postgresql+psycopg2://{quote_plus(user)}{pw}@{host}:{port}/{name}{query}"

    # Try to read from Settings if project config provides it
    try:
        from packages.core.config import load_settings

        s = load_settings()
        if str(s.database_url):
            return str(s.database_url)
    except Exception:
        pass

    # Fallback to ini value (works with DATABASE__* variables in .env)
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    ini_section = config.get_section(config.config_ini_section) or {}
    ini_section["sqlalchemy.url"] = _get_db_url()
    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:  # type: Connection
        context.configure(
            connection=connection,
            target_metadata=None,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
