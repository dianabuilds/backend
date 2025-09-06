from __future__ import annotations

from alembic import op

revision = "20241206_transition_fk_ondelete"
down_revision = "20241205_node_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS node_transitions_from_node_id_fkey"
    )
    op.execute(
        "ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS fk_node_transitions_from_node_id_nodes"
    )
    op.create_foreign_key(
        "fk_node_transitions_from_node_id_nodes",
        "node_transitions",
        "nodes",
        ["from_node_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        "ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS node_transitions_to_node_id_fkey"
    )
    op.execute(
        "ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS fk_node_transitions_to_node_id_nodes"
    )
    op.create_foreign_key(
        "fk_node_transitions_to_node_id_nodes",
        "node_transitions",
        "nodes",
        ["to_node_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_node_transitions_from_node_id_nodes",
        "node_transitions",
        type_="foreignkey",
    )
    op.execute(
        "ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS node_transitions_from_node_id_fkey"
    )
    op.create_foreign_key(
        "fk_node_transitions_from_node_id_nodes",
        "node_transitions",
        "nodes",
        ["from_node_id"],
        ["id"],
    )

    op.drop_constraint(
        "fk_node_transitions_to_node_id_nodes",
        "node_transitions",
        type_="foreignkey",
    )
    op.execute(
        "ALTER TABLE node_transitions DROP CONSTRAINT IF EXISTS node_transitions_to_node_id_fkey"
    )
    op.create_foreign_key(
        "fk_node_transitions_to_node_id_nodes",
        "node_transitions",
        "nodes",
        ["to_node_id"],
        ["id"],
    )
