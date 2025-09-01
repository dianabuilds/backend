from __future__ import annotations

from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "20260101_node_tags_node_id_bigint"
down_revision = "20251231_backfill_nodes_without_content_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("node_tags", "node_id", new_column_name="node_uuid")
    op.add_column(
        "node_tags",
        sa.Column("node_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "node_tags_node_id_fkey",
        "node_tags",
        "nodes",
        ["node_id"],
        ["id"],
        ondelete="CASCADE",
    )

    sql_path = (
        Path(__file__).resolve().parents[4] / "scripts" / "sql" / "fk_uuid_to_id.sql"
    )
    op.execute(sql_path.read_text())
    op.execute("CALL backfill_fk_id('node_tags', 'tag_id', 'node_uuid', 'node_id')")
    op.execute(
        """
        CREATE TRIGGER fill_node_tags_node_id
        BEFORE INSERT OR UPDATE ON node_tags
        FOR EACH ROW EXECUTE FUNCTION fill_fk_id_from_uuid('node_id', 'node_uuid')
        """
    )
    op.execute(
        """
        CREATE TRIGGER prevent_node_tags_node_uuid_write
        BEFORE INSERT OR UPDATE ON node_tags
        FOR EACH ROW EXECUTE FUNCTION prevent_uuid_write('node_uuid', 'node_id')
        """
    )

    op.alter_column("node_tags", "node_id", nullable=False)
    op.drop_constraint("node_tags_pkey", "node_tags", type_="primary")
    op.create_primary_key("node_tags_pkey", "node_tags", ["node_id", "tag_id"])


def downgrade() -> None:
    op.drop_constraint("node_tags_pkey", "node_tags", type_="primary")
    op.create_primary_key("node_tags_pkey", "node_tags", ["node_uuid", "tag_id"])
    op.execute("DROP TRIGGER IF EXISTS prevent_node_tags_node_uuid_write ON node_tags")
    op.execute("DROP TRIGGER IF EXISTS fill_node_tags_node_id ON node_tags")
    op.alter_column("node_tags", "node_id", nullable=True)
    op.drop_constraint("node_tags_node_id_fkey", "node_tags", type_="foreignkey")
    op.drop_column("node_tags", "node_id")
    op.alter_column("node_tags", "node_uuid", new_column_name="node_id")
