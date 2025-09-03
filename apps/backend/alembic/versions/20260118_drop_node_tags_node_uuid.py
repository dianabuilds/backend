from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260118_drop_node_tags_node_uuid"
down_revision = "20260117_drop_nodes_alt_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS fill_node_tags_node_id ON node_tags")
    op.execute("DROP TRIGGER IF EXISTS prevent_node_tags_node_uuid_write ON node_tags")
    op.drop_column("node_tags", "node_uuid")


def downgrade() -> None:
    op.add_column(
        "node_tags",
        sa.Column(
            "node_uuid", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
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
