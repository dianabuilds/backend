from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20241206_transition_fk_ondelete"
down_revision = "20241205_node_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("node_transitions") as batch:
        batch.drop_constraint(
            "node_transitions_from_node_id_fkey",
            type_="foreignkey",
            if_exists=True,
        )
        batch.create_foreign_key(
            "node_transitions_from_node_id_fkey",
            "nodes",
            ["from_node_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.drop_constraint(
            "node_transitions_to_node_id_fkey",
            type_="foreignkey",
            if_exists=True,
        )
        batch.create_foreign_key(
            "node_transitions_to_node_id_fkey",
            "nodes",
            ["to_node_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    with op.batch_alter_table("node_transitions") as batch:
        batch.drop_constraint(
            "node_transitions_from_node_id_fkey",
            type_="foreignkey",
            if_exists=True,
        )
        batch.create_foreign_key(
            "node_transitions_from_node_id_fkey",
            "nodes",
            ["from_node_id"],
            ["id"],
        )
        batch.drop_constraint(
            "node_transitions_to_node_id_fkey",
            type_="foreignkey",
            if_exists=True,
        )
        batch.create_foreign_key(
            "node_transitions_to_node_id_fkey",
            "nodes",
            ["to_node_id"],
            ["id"],
        )
