"""
Add embedding vector column to nodes

Revision ID: 0015
Revises: 0014
Create Date: 2025-09-21
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def upgrade() -> None:
    base = Path(__file__).resolve().parents[2]
    sql_file = base / "domains" / "product" / "nodes" / "schema" / "sql" / "008_nodes_embedding.sql"
    op.execute(_read_sql(sql_file))


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_nodes_embedding")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS embedding")
