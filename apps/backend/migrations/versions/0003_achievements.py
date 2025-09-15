"""
Add product achievements tables

Revision ID: 0003
Revises: 0002
Create Date: 2025-09-15

"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def upgrade() -> None:
    base = Path(__file__).resolve().parents[2]  # apps/apps/backend
    files = [
        base
        / "domains"
        / "product"
        / "achievements"
        / "schema"
        / "sql"
        / "001_achievements.sql",
        base
        / "domains"
        / "product"
        / "achievements"
        / "schema"
        / "sql"
        / "002_achievement_grants.sql",
    ]
    for f in files:
        sql = _read_sql(f)
        if sql.strip():
            op.execute(sql)


def downgrade() -> None:
    drops = [
        "DROP TABLE IF EXISTS product_achievement_grants CASCADE",
        "DROP TABLE IF EXISTS product_achievements CASCADE",
    ]
    for stmt in drops:
        op.execute(stmt)
