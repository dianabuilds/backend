from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20241210_slug_scoped_by_workspace"
# Ensure a linear migration chain; previously this revision incorrectly
# referenced `20241201_user_profiles` as an additional ancestor which
# caused Alembic to report overlapping revisions during upgrades.
down_revision = "20241206_transition_fk_ondelete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    node_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("nodes")
    }
    if "nodes_slug_key" in node_constraints:
        op.drop_constraint("nodes_slug_key", "nodes", type_="unique")

    op.create_index(
        "ix_nodes_account_id_slug",
        "nodes",
        ["account_id", "slug"],
        unique=True,
    )
    op.create_index(
        "ix_nodes_account_id_created_at",
        "nodes",
        ["account_id", "created_at"],
    )

    content_constraints = {
        constraint["name"] for constraint in inspector.get_unique_constraints("content_items")
    }
    if "content_items_slug_key" in content_constraints:
        op.drop_constraint("content_items_slug_key", "content_items", type_="unique")

    op.create_index(
        "ix_content_items_workspace_id_slug",
        "content_items",
        ["workspace_id", "slug"],
        unique=True,
    )
    op.create_index(
        "ix_content_items_workspace_id_created_at",
        "content_items",
        ["workspace_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_content_items_workspace_id_created_at",
        table_name="content_items",
    )
    op.drop_index(
        "ix_content_items_workspace_id_slug",
        table_name="content_items",
    )
    op.create_unique_constraint(
        "content_items_slug_key",
        "content_items",
        ["slug"],
    )

    op.drop_index(
        "ix_nodes_account_id_created_at",
        table_name="nodes",
    )
    op.drop_index(
        "ix_nodes_account_id_slug",
        table_name="nodes",
    )
    op.create_unique_constraint(
        "nodes_slug_key",
        "nodes",
        ["slug"],
    )
