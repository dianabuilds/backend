from __future__ import annotations

import logging
from logging.config import fileConfig

import os
from alembic import context
from sqlalchemy import engine_from_config, pool

# Interpret the config file for Python logging.
config = context.config
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

    # Try to read from Settings, but only if it overrides default via APP_DATABASE_URL
    try:
        from packages.core.config import load_settings

        s = load_settings()
        # If env provides APP_DATABASE_URL, Settings would pick it; otherwise
        # prefer alembic.ini interpolation of DATABASE__* vars.
        if os.getenv("APP_DATABASE_URL"):
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
