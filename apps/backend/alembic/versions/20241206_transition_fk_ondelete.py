from __future__ import annotations

from alembic import op

revision = "20241206_transition_fk_ondelete"
down_revision = "20241205_node_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "node_transitions_from_node_id_fkey",
        "node_transitions",
        type_="foreignkey",
        if_exists=True,
    )
    op.drop_constraint(
        "fk_node_transitions_from_node_id_nodes",
        "node_transitions",
        type_="foreignkey",
        if_exists=True,
    )
    op.create_foreign_key(
        "fk_node_transitions_from_node_id_nodes",
        "node_transitions",
        "nodes",
        ["from_node_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "node_transitions_to_node_id_fkey",
        "node_transitions",
        type_="foreignkey",
        if_exists=True,
    )
    op.drop_constraint(
        "fk_node_transitions_to_node_id_nodes",
        "node_transitions",
        type_="foreignkey",
        if_exists=True,
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
        if_exists=True,
    )
    op.drop_constraint(
        "node_transitions_from_node_id_fkey",
        "node_transitions",
        type_="foreignkey",
        if_exists=True,
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
        if_exists=True,
    )
    op.drop_constraint(
        "node_transitions_to_node_id_fkey",
        "node_transitions",
        type_="foreignkey",
        if_exists=True,
    )
    op.create_foreign_key(
        "fk_node_transitions_to_node_id_nodes",
        "node_transitions",
        "nodes",
        ["to_node_id"],
        ["id"],
    )
