from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine


def run_migrations_online() -> None:  # pragma: no cover - template
    cfg = context.config
    x = context.get_x_argument(as_dictionary=True)
    db_url = cfg.get_main_option("sqlalchemy.url") or x.get("db_url")
    assert db_url, "db_url required"
    schema = "<your_domain>"
    version_table = f"alembic_version_{schema}"
    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        context.configure(
            connection=conn,
            target_metadata=None,
            version_table=version_table,
            version_table_schema=schema,
            include_schemas=True,
        )
        conn.exec_driver_sql(f'SET search_path TO "{schema}"')
        context.run_migrations()


run_migrations_online()
