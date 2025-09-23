"""
Resize node embedding vector column to 1536 dimensions

Revision ID: 0016
Revises: 0015
Create Date: 2025-09-22
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def upgrade() -> None:
    base = Path(__file__).resolve().parents[2]
    sql_file = (
        base / "domains" / "product" / "nodes" / "schema" / "sql" / "009_nodes_embedding_resize.sql"
    )
    op.execute(_read_sql(sql_file))


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_nodes_embedding")
    op.execute("ALTER TABLE nodes DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE nodes ADD COLUMN embedding vector(384)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_nodes_embedding ON nodes USING ivfflat (embedding vector_l2_ops) WITH (lists = 100)"
    )
