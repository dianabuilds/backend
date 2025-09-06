from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20250201_remove_spaces"
down_revision = "20241215_drop_workspace_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop legacy space-based indexes and column
    with op.batch_alter_table("nodes") as batch:
        batch.drop_index("ix_nodes_space_id_slug")
        batch.drop_index("ix_nodes_space_id_created_at")
        batch.drop_column("space_id")

    op.add_column("node_transitions", sa.Column("account_id", sa.BigInteger(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE node_transitions AS nt
            SET account_id = n.account_id
            FROM nodes AS n
            WHERE nt.from_node_id = n.id
            """
        )
    )
    op.alter_column("node_transitions", "account_id", nullable=False)
    op.create_foreign_key(
        "fk_node_transitions_account_id_accounts",
        "node_transitions",
        "accounts",
        ["account_id"],
        ["id"],
    )
    op.create_index(
        "ix_node_transitions_account_id_created_at",
        "node_transitions",
        ["account_id", "created_at"],
    )
    op.drop_index("ix_node_transitions_space_id_created_at", table_name="node_transitions")
    op.drop_constraint(
        "fk_node_transitions_space_id_spaces", "node_transitions", type_="foreignkey"
    )
    op.drop_column("node_transitions", "space_id")

    op.add_column("navigation_cache", sa.Column("account_id", sa.BigInteger(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE navigation_cache AS nc
            SET account_id = n.account_id
            FROM nodes AS n
            WHERE nc.node_slug = n.slug
            """
        )
    )
    op.alter_column("navigation_cache", "account_id", nullable=False)
    op.create_foreign_key(
        "fk_navigation_cache_account_id_accounts",
        "navigation_cache",
        "accounts",
        ["account_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_nav_cache_account_slug",
        "navigation_cache",
        ["account_id", "node_slug"],
    )
    op.create_index(
        "ix_navigation_cache_account_id_generated_at",
        "navigation_cache",
        ["account_id", "generated_at"],
    )
    op.drop_index("ix_navigation_cache_space_id_generated_at", table_name="navigation_cache")
    op.drop_constraint("uq_nav_cache_space_slug", "navigation_cache", type_="unique")
    op.drop_constraint(
        "fk_navigation_cache_space_id_spaces", "navigation_cache", type_="foreignkey"
    )
    op.drop_column("navigation_cache", "space_id")

    op.drop_table("space_members")
    op.drop_table("spaces")


def downgrade() -> None:
    raise NotImplementedError("downgrade not supported")
