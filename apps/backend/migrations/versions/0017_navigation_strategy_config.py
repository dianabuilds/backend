"""
Create navigation strategy config

Revision ID: 0017
Revises: 0016
Create Date: 2025-09-22
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def upgrade() -> None:
    base = Path(__file__).resolve().parents[2]
    sql_file = (
        base
        / "domains"
        / "product"
        / "navigation"
        / "schema"
        / "sql"
        / "001_navigation_strategy_config.sql"
    )
    op.execute(_read_sql(sql_file))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS navigation_strategy_config")
